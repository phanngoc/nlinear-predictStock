"""
Chatbot Service for News Q&A.
Uses LlamaIndex for RAG-based question answering over news data.
"""
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import streamlit as st

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings as LlamaSettings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.base.llms.types import MessageRole

from config import settings


class ChatbotService:
    """
    RAG-based chatbot service for news Q&A.
    Loads documents from trend_news/output/{date}/txt/ folder.
    """
    
    def __init__(self):
        """Initialize the chatbot service with OpenAI LLM."""
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY is not set. Please update .env file.")
        
        LlamaSettings.llm = OpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Cache indexes by date_str
        self.indexes: Dict[str, VectorStoreIndex] = {}
        # Current loaded index
        self.current_index: Optional[VectorStoreIndex] = None
        self.current_date: Optional[str] = None
        
    def get_news_data_path(self) -> Path:
        """Get absolute path to news data folder."""
        base_path = Path(__file__).parent.parent / settings.NEWS_DATA_PATH
        return base_path.resolve()
    
    def get_available_dates(self) -> List[str]:
        """
        Get list of available dates from output folder.
        
        Returns:
            List of date folder names sorted in descending order (newest first).
        """
        data_path = self.get_news_data_path()
        if not data_path.exists():
            return []
        
        dates = []
        for folder in data_path.iterdir():
            if folder.is_dir() and (folder / "txt").exists():
                dates.append(folder.name)
        
        # Sort descending (newest first)
        return sorted(dates, reverse=True)
    
    def get_txt_files(self, date_str: str) -> List[Path]:
        """
        Get list of .txt files for a given date.
        
        Args:
            date_str: Date folder name (e.g., "2025năm12tháng14ngày")
            
        Returns:
            List of .txt file paths sorted by name.
        """
        data_path = self.get_news_data_path()
        txt_path = data_path / date_str / "txt"
        
        if not txt_path.exists():
            return []
        
        return sorted(txt_path.glob("*.txt"))
    
    def load_documents(self, date_str: str) -> bool:
        """
        Load documents for a specific date.
        
        Args:
            date_str: Date folder name (e.g., "2025năm12tháng14ngày")
            
        Returns:
            True if documents were loaded successfully, False otherwise.
        """
        # Check cache first
        if date_str in self.indexes:
            self.current_index = self.indexes[date_str]
            self.current_date = date_str
            return True
        
        txt_files = self.get_txt_files(date_str)
        if not txt_files:
            return False
        
        # Load latest file (or all files if preferred)
        latest_file = txt_files[-1]
        
        try:
            documents = SimpleDirectoryReader(input_files=[str(latest_file)]).load_data()
            
            self.current_index = VectorStoreIndex.from_documents(
                documents,
                transformations=[SentenceSplitter(chunk_size=settings.CHUNK_SIZE)]
            )
            
            # Cache the index
            self.indexes[date_str] = self.current_index
            self.current_date = date_str
            
            return True
        except Exception as e:
            st.error(f"Error loading documents: {str(e)}")
            return False
    
    def chat(
        self, 
        question: str, 
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
        Chat with the chatbot using conversation history.
        
        Args:
            question: User's question
            chat_history: List of {"role": "user"|"assistant", "content": "..."}
            
        Returns:
            Assistant's response
        """
        if not self.current_index:
            raise ValueError("No documents loaded. Call load_documents first.")
        
        # Convert chat history to ChatMessage format
        chat_messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                role = MessageRole.USER
            elif msg["role"] == "assistant":
                role = MessageRole.ASSISTANT
            else:
                continue
            chat_messages.append(ChatMessage(role=role, content=msg["content"]))
        
        # Create memory buffer with history
        memory = ChatMemoryBuffer.from_defaults(chat_history=chat_messages)
        
        # Create chat engine with memory
        chat_engine = self.current_index.as_chat_engine(
            chat_mode="context",
            memory=memory,
            verbose=False
        )
        
        # Get response
        response = chat_engine.chat(question)
        return str(response)
    
    def query(self, question: str) -> str:
        """
        Simple query without conversation history.
        
        Args:
            question: User's question
            
        Returns:
            Response from the query engine
        """
        if not self.current_index:
            raise ValueError("No documents loaded. Call load_documents first.")
        
        query_engine = self.current_index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
    
    def get_document_preview(self, date_str: str, max_lines: int = 100) -> str:
        """
        Get preview of document content for a given date.
        
        Args:
            date_str: Date folder name
            max_lines: Maximum number of lines to return
            
        Returns:
            Preview text content
        """
        txt_files = self.get_txt_files(date_str)
        if not txt_files:
            return "No documents found."
        
        latest_file = txt_files[-1]
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[:max_lines]
            return "".join(lines)
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def clear_cache(self, date_str: Optional[str] = None):
        """
        Clear cached indexes.
        
        Args:
            date_str: If None, clear all. Otherwise, clear only the specified date.
        """
        if date_str is None:
            self.indexes.clear()
            self.current_index = None
            self.current_date = None
        elif date_str in self.indexes:
            del self.indexes[date_str]
            if self.current_date == date_str:
                self.current_index = None
                self.current_date = None


@st.cache_resource
def get_chatbot_service() -> ChatbotService:
    """Get cached chatbot service instance."""
    return ChatbotService()
