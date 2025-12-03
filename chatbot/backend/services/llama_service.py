from pathlib import Path
from typing import Optional, Dict, List
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.base.llms.types import MessageRole
from core.config import settings
from core.database import SessionLocal
from models.db_models import Message

class LlamaService:
    def __init__(self):
        Settings.llm = OpenAI(model="gpt-4o", temperature=0.1, api_key=settings.OPENAI_API_KEY)
        self.index = None
        # Cache indexes theo date_str
        self.indexes: Dict[str, VectorStoreIndex] = {}
        # Cache chat engines theo thread_id
        self.chat_engines: Dict[int, any] = {}
        
    def load_documents(self, date_str: str):
        """
        Load .txt files from output/{date}/txt/ folder.
        Hỗ trợ cả 2 format: {YYYY}năm{MM}tháng{DD}ngày và {YYYY}年{MM}月{DD}日
        """
        # Thử format mới trước
        path = Path(settings.NEWS_DATA_PATH) / date_str / "txt"
        
        # Nếu không tồn tại, thử format cũ
        if not path.exists():
            # Convert từ format mới sang format cũ nếu cần
            if "năm" in date_str and "tháng" in date_str and "ngày" in date_str:
                # Format: 2025năm11tháng27ngày -> 2025年11月27日
                parts = date_str.replace("năm", " ").replace("tháng", " ").replace("ngày", "").split()
                if len(parts) == 3:
                    date_str_old = f"{parts[0]}年{parts[1]}月{parts[2]}日"
                    path = Path(settings.NEWS_DATA_PATH) / date_str_old / "txt"
            elif "年" in date_str and "月" in date_str and "日" in date_str:
                # Format: 2025年11月27日 -> 2025năm11tháng27ngày
                parts = date_str.replace("年", " ").replace("月", " ").replace("日", "").split()
                if len(parts) == 3:
                    date_str_new = f"{parts[0]}năm{parts[1]}tháng{parts[2]}ngày"
                    path = Path(settings.NEWS_DATA_PATH) / date_str_new / "txt"
        
        if not path.exists():
            raise FileNotFoundError(f"No data found for date: {date_str}")
        
        txt_files = sorted(path.glob("*.txt"))
        if not txt_files:
            raise FileNotFoundError(f"No .txt files found in {path}")
        
        # Cache index theo date_str để tránh load lại
        if date_str in self.indexes:
            self.index = self.indexes[date_str]
            return
        
        latest_file = txt_files[-1]
        documents = SimpleDirectoryReader(input_files=[str(latest_file)]).load_data()
        
        self.index = VectorStoreIndex.from_documents(
            documents,
            transformations=[SentenceSplitter(chunk_size=512)]
        )
        print(f"Loaded documents for {latest_file}")
        # Cache index
        self.indexes[date_str] = self.index
        
    def _load_messages_from_db(self, thread_id: int) -> List[ChatMessage]:
        """
        Load conversation history từ database cho thread_id.
        
        Args:
            thread_id: ID của thread
            
        Returns:
            List[ChatMessage]: Danh sách messages đã convert sang ChatMessage format
        """
        db = SessionLocal()
        try:
            messages = db.query(Message).filter(
                Message.thread_id == thread_id
            ).order_by(Message.created_at.asc()).all()
            
            chat_messages = []
            for msg in messages:
                if msg.role == "user":
                    role = MessageRole.USER
                elif msg.role == "assistant":
                    role = MessageRole.ASSISTANT
                else:
                    continue  # Bỏ qua các role khác
                
                chat_messages.append(
                    ChatMessage(role=role, content=msg.content)
                )
            
            return chat_messages
        finally:
            db.close()
    
    def get_or_create_chat_engine(self, thread_id: int, date_str: str):
        """
        Lấy hoặc tạo chat engine cho thread_id.
        Chat engine sẽ có conversation history từ database.
        
        Args:
            thread_id: ID của thread
            date_str: Date string để load documents
            
        Returns:
            Chat engine instance
        """
        # Kiểm tra cache
        if thread_id in self.chat_engines:
            return self.chat_engines[thread_id]
        
        # Load documents nếu chưa có index
        if date_str not in self.indexes:
            self.load_documents(date_str)
        
        index = self.indexes[date_str]
        
        # Load conversation history từ database
        chat_messages = self._load_messages_from_db(thread_id)
        
        # Tạo ChatMemoryBuffer với history
        memory = ChatMemoryBuffer.from_defaults(chat_history=chat_messages)
        
        # Tạo chat engine với memory
        chat_engine = index.as_chat_engine(
            chat_mode="context",
            memory=memory,
            verbose=True
        )
        
        # Cache chat engine
        self.chat_engines[thread_id] = chat_engine
        
        return chat_engine
    
    def chat(self, thread_id: int, question: str, date_str: str) -> str:
        """
        Chat với chat engine có conversation history.
        
        Args:
            thread_id: ID của thread
            question: Câu hỏi của user
            date_str: Date string để load documents
            
        Returns:
            str: Câu trả lời từ chat engine
        """
        chat_engine = self.get_or_create_chat_engine(thread_id, date_str)
        response = chat_engine.chat(question)
        return str(response)
        
    def query(self, question: str) -> str:
        """
        Query đơn giản không có conversation history (backward compatibility).
        """
        if not self.index:
            raise ValueError("Documents not loaded. Call load_documents first.")
        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
        
    def summarize_by_keywords(self, keywords: list[str]) -> dict:
        summaries = {}
        for keyword in keywords:
            prompt = f"Summarize all news related to '{keyword}'. Include original links if available."
            try:
                summary = self.query(prompt)
                summaries[keyword] = summary
            except Exception as e:
                summaries[keyword] = f"Error generating summary: {str(e)}"
        return summaries
    
    def clear_chat_engine_cache(self, thread_id: Optional[int] = None):
        """
        Xóa cache của chat engine.
        
        Args:
            thread_id: Nếu None, xóa tất cả. Nếu có giá trị, chỉ xóa chat engine của thread đó.
        """
        if thread_id is None:
            self.chat_engines.clear()
        elif thread_id in self.chat_engines:
            del self.chat_engines[thread_id]

llama_service = LlamaService()
