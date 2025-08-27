"""
Application configuration settings
"""
import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic settings
    PROJECT_NAME: str = "Multi-Agent Development System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Ollama Model settings
    MODEL_NAME: str = "mistral:7b-instruct"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    MODEL_MAX_TOKENS: int = 4096
    MODEL_TEMPERATURE: float = 0.7
    MODEL_TOP_P: float = 0.9
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_CONNECTIONS: int = 10
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Agent settings
    MAX_ITERATIONS: int = 10
    TIMEOUT_SECONDS: int = 300
    MAX_CONCURRENT_WORKFLOWS: int = 5
    
    # File system settings
    WORKSPACE_DIR: str = "workspace"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".scss",
        ".json", ".yaml", ".yml", ".md", ".txt", ".sh", ".sql"
    ]
    
    @field_validator("OLLAMA_BASE_URL", mode="before")
    @classmethod
    def set_ollama_url(cls, v):
        if v is None:
            return "http://localhost:11434"
        return v
    
    @field_validator("MODEL_NAME", mode="before")
    @classmethod
    def set_model_name(cls, v):
        if v is None:
            return "mistral:7b-instruct"
        return v
    
    @field_validator("WORKSPACE_DIR", mode="before")
    @classmethod
    def set_workspace_dir(cls, v):
        workspace = Path(v)
        workspace.mkdir(exist_ok=True)
        return str(workspace.absolute())
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env"
    }


# Global settings instance
settings = Settings()