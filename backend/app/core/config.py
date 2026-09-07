import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Automated Minutes of Meeting (MoM) Generator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "mom-super-secure-production-secret-key-change-in-prod-987654321")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database configuration (PostgreSQL primary, SQLite local fallback)
    POSTGRES_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/mom_db")
    SQLITE_URL: str = "sqlite+aiosqlite:///./mom_app.db"
    
    # Upload and export directories
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "uploads")
    EXPORT_DIR: str = os.path.join(BASE_DIR, "exports")
    
    # ML Models configurations
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    DEBERTA_MODEL_NAME: str = "microsoft/deberta-v3-base"
    NER_MODEL_NAME: str = "dslim/bert-base-NER"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    QWEN_MODEL_NAME: str = "Qwen/Qwen2.5-3B-Instruct"

    class Config:
        case_sensitive = True

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
