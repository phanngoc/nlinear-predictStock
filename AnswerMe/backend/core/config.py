from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

# Load .env file từ backend/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/newsdb"
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    OPENAI_API_KEY: str = ""
    NEWS_DATA_PATH: str = "../../TrendNews/output"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
