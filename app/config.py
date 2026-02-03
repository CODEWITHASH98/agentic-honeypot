from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    MESSAGE: str = "Agentic Honey-Pot API"
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"
    API_SECRET_KEY: str = "dev-secret-key"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
