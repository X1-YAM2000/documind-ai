"""
Configuration settings for DocuMind AI
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # Remove in production
    ]
    
    # Ollama API Configuration
    OLLAMA_API_URL: str = "http://localhost:11434/api/chat"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # Document Processing
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    
    # RAG Configuration
    TOP_K_CHUNKS: int = 4
    MAX_CONVERSATION_HISTORY: int = 6
    
    # AI Configuration
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
