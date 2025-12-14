"""
Configuration for Trading System Chatbot.
Load environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

# Load .env file từ trading_system/.env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    OPENAI_API_KEY: str = ""
    NEWS_DATA_PATH: str = "../trend_news/output"
    
    # LLM Settings
    LLM_MODEL: str = "gpt-5"
    LLM_TEMPERATURE: float = 0.1
    
    # RAG Settings
    CHUNK_SIZE: int = 512
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
