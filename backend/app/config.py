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

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_EXPIRATION_DAYS: int = 30

    # OpenAI (optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"

    # Scoring Algorithm Configuration
    SCORING_STRATEGY: str = "additive_weighted"  # Default strategy
    SCORING_IMPACT_WEIGHT: float = 2.0
    SCORING_URGENCY_WEIGHT: float = 1.5
    SCORING_STRATEGIC_NUDGE_BOOST: float = 1.5
    SCORING_DAMPENING_FACTOR: float = 0.5
    SCORING_PRIORITY_MULTIPLIER: float = 2.0

    # Value mappings (impact and urgency to numeric values)
    SCORING_IMPACT_VALUES: dict[str, int] = {"A": 4, "B": 3, "C": 2, "D": 1}
    SCORING_URGENCY_VALUES: dict[int, int] = {1: 4, 2: 3, 3: 2, 4: 1}

    @property
    def SCORING_CONFIG(self) -> dict:
        """Combined scoring configuration.

        Returns:
            Dictionary with all scoring parameters for strategy use
        """
        return {
            "impact_weight": self.SCORING_IMPACT_WEIGHT,
            "urgency_weight": self.SCORING_URGENCY_WEIGHT,
            "strategic_nudge_boost": self.SCORING_STRATEGIC_NUDGE_BOOST,
            "dampening_factor": self.SCORING_DAMPENING_FACTOR,
            "priority_multiplier": self.SCORING_PRIORITY_MULTIPLIER,
            "impact_values": self.SCORING_IMPACT_VALUES,
            "urgency_values": self.SCORING_URGENCY_VALUES,
        }

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
