from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Absolute path to the backend directory
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    # PostgreSQL configuration
    DATABASE_URL: str

    # Authentication configuration
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Project upload configuration
    UPLOAD_DIR: str = "app/storage/projects"
    MAX_UPLOAD_SIZE_MB: int = 100

    # Local AI configuration
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:3b"

    # Load environment variables from backend/.env
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Create one settings object for the application
settings = Settings()
