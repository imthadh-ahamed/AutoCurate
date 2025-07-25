"""
AutoCurate Configuration Management
Centralized configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(default="sqlite:///./autocurate.db", env="DATABASE_URL")
    pool_size: int = Field(default=10, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DATABASE_MAX_OVERFLOW")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class LLMSettings(BaseSettings):
    """LLM and AI configuration"""
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class VectorDBSettings(BaseSettings):
    """Vector database configuration"""
    type: str = Field(default="faiss", env="VECTOR_DB_TYPE")  # faiss, pinecone, chroma
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    chroma_host: str = Field(default="localhost", env="CHROMA_HOST")
    chroma_port: int = Field(default=8000, env="CHROMA_PORT")
    collection_name: str = Field(default="autocurate_content", env="VECTOR_COLLECTION_NAME")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class ScrapingSettings(BaseSettings):
    """Web scraping configuration"""
    delay: float = Field(default=1.0, env="SCRAPER_DELAY")
    concurrent_requests: int = Field(default=16, env="SCRAPER_CONCURRENT_REQUESTS")
    user_agent: str = Field(
        default="AutoCurate/1.0 (+https://github.com/your-username/autocurate)", 
        env="SCRAPER_USER_AGENT"
    )
    timeout: int = Field(default=30, env="SCRAPER_TIMEOUT")
    max_retries: int = Field(default=3, env="SCRAPER_MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class ContentSettings(BaseSettings):
    """Content processing configuration"""
    max_content_length: int = Field(default=10000, env="MAX_CONTENT_LENGTH")
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    min_text_length: int = Field(default=100, env="MIN_TEXT_LENGTH")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class SchedulingSettings(BaseSettings):
    """Task scheduling configuration"""
    ingestion_schedule_minutes: int = Field(default=60, env="INGESTION_SCHEDULE_MINUTES")
    cleanup_schedule_hours: int = Field(default=24, env="CLEANUP_SCHEDULE_HOURS")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class AppSettings(BaseSettings):
    """Main application configuration"""
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    secret_key: str = Field(env="SECRET_KEY")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Rate limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Monitoring
    prometheus_port: int = Field(default=8001, env="PROMETHEUS_PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


class Settings:
    """Centralized settings container"""
    
    def __init__(self):
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.llm = LLMSettings()
        self.vector_db = VectorDBSettings()
        self.scraping = ScrapingSettings()
        self.content = ContentSettings()
        self.scheduling = SchedulingSettings()


# Global settings instance
settings = Settings()
