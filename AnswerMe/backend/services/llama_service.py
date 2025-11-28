from pathlib import Path
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.openai import OpenAI
from core.config import settings

class LlamaService:
    def __init__(self):
        self.llm = OpenAI(model="gpt-4", temperature=0.1, api_key=settings.OPENAI_API_KEY)
        self.index = None
        
    def load_documents(self, date_str: str):
        """Load .txt files from output/{date}/txt/ folder"""
        path = Path(settings.NEWS_DATA_PATH) / date_str / "txt"
        
        if not path.exists():
            raise FileNotFoundError(f"No data found for date: {date_str}")
        
        txt_files = sorted(path.glob("*.txt"))
        if not txt_files:
            raise FileNotFoundError(f"No .txt files found in {path}")
        
        latest_file = txt_files[-1]
        documents = SimpleDirectoryReader(input_files=[str(latest_file)]).load_data()
        
        self.index = VectorStoreIndex.from_documents(
            documents,
            node_parser=SentenceSplitter(chunk_size=512)
        )
        
    def query(self, question: str) -> str:
        if not self.index:
            raise ValueError("Documents not loaded. Call load_documents first.")
        query_engine = self.index.as_query_engine(llm=self.llm)
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

llama_service = LlamaService()
