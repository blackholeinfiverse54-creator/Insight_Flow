from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    
    # Application Configuration
    APP_NAME: str = "InsightFlow"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Q-Learning Hyperparameters
    LEARNING_RATE: float = 0.1
    DISCOUNT_FACTOR: float = 0.95
    EPSILON: float = 0.1
    MIN_EPSILON: float = 0.01
    EPSILON_DECAY: float = 0.995
    
    # Core Feedback Service Configuration
    CORE_FEEDBACK_SERVICE_URL: str = os.getenv(
        "CORE_FEEDBACK_SERVICE_URL",
        "http://core-feedback:8000/api/scores"
    )
    CORE_FEEDBACK_CACHE_TTL: int = int(os.getenv(
        "CORE_FEEDBACK_CACHE_TTL",
        "30"
    ))
    CORE_FEEDBACK_TIMEOUT: int = int(os.getenv(
        "CORE_FEEDBACK_TIMEOUT",
        "5"
    ))
    CORE_FEEDBACK_MAX_RETRIES: int = int(os.getenv(
        "CORE_FEEDBACK_MAX_RETRIES",
        "3"
    ))
    
    # Routing Decision Logging
    ROUTING_LOG_DIR: str = os.getenv(
        "ROUTING_LOG_DIR",
        "logs"
    )
    ROUTING_LOG_RETENTION_DAYS: int = int(os.getenv(
        "ROUTING_LOG_RETENTION_DAYS",
        "30"
    ))
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create global settings instance
settings = Settings()