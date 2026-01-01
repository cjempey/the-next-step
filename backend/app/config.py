"""
Application configuration from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    DATABASE_URL: str = "postgresql+psycopg://user:password@localhost/the_next_step"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure DATABASE_URL uses psycopg driver for psycopg3 compatibility
        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",  # Web dev
        "http://localhost:5173",  # Vite default
        "http://localhost:8081",  # React Native dev
    ]

    # OpenAI (optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
