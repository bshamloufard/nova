"""Configuration management for Nova backend."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    deepgram_api_key: str = ""
    assemblyai_api_key: str = ""
    openai_api_key: str = ""
    
    # Application settings
    app_name: str = "Nova Transcription"
    debug: bool = True
    
    # File storage
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 100
    
    # Transcription settings
    confidence_threshold: float = 0.75
    context_window_words: int = 50
    min_segment_duration_ms: int = 500
    max_segment_duration_ms: int = 10000
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def load_api_keys_from_file(filepath: str = "api.md") -> None:
    """Load API keys from the api.md file format."""
    global settings
    
    if not os.path.exists(filepath):
        return
    
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == "deepgram":
                    settings.deepgram_api_key = value
                elif key == "assemblyai":
                    settings.assemblyai_api_key = value
                elif key == "openai":
                    settings.openai_api_key = value

