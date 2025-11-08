from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with Sovereign Core integration"""
    
    # ========================================================================
    # Sovereign Core Configuration (Phase 2.2)
    # ========================================================================
    
    # Sovereign Core Auth
    SOVEREIGN_AUTH_URL: str = os.getenv(
        "SOVEREIGN_AUTH_URL",
        "http://localhost:8003/auth"
    )
    SOVEREIGN_SERVICE_KEY: str = os.getenv(
        "SOVEREIGN_SERVICE_KEY",
        "sovereign-service-key-placeholder"
    )
    SOVEREIGN_JWT_SECRET: str = os.getenv(
        "SOVEREIGN_JWT_SECRET",
        "sovereign-jwt-secret-placeholder"
    )
    SOVEREIGN_JWT_ALGORITHM: str = os.getenv(
        "SOVEREIGN_JWT_ALGORITHM",
        "HS256"
    )
    
    # Sovereign Core Database
    SOVEREIGN_DB_HOST: str = os.getenv(
        "SOVEREIGN_DB_HOST",
        "localhost"
    )
    SOVEREIGN_DB_PORT: int = int(os.getenv(
        "SOVEREIGN_DB_PORT",
        "5432"
    ))
    SOVEREIGN_DB_NAME: str = os.getenv(
        "SOVEREIGN_DB_NAME",
        "sovereign_core"
    )
    SOVEREIGN_DB_USER: str = os.getenv(
        "SOVEREIGN_DB_USER",
        "sovereign_user"
    )
    SOVEREIGN_DB_PASSWORD: str = os.getenv(
        "SOVEREIGN_DB_PASSWORD",
        "sovereign_password"
    )
    
    # Migration toggle
    USE_SOVEREIGN_CORE: bool = os.getenv(
        "USE_SOVEREIGN_CORE",
        "false"
    ).lower() == "true"
    
    # Backward compatibility (Supabase)
    # These are kept for transition period
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")
    
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
    
    # ========================================================================
    # STP-Layer Configuration (Phase 2.2)
    # ========================================================================
    
    # Enable/disable STP wrapping (for gradual rollout)
    STP_ENABLED: bool = os.getenv("STP_ENABLED", "true").lower() == "true"
    
    # STP destination system
    STP_DESTINATION: str = os.getenv("STP_DESTINATION", "sovereign_core")
    
    # Default STP priority
    STP_DEFAULT_PRIORITY: str = os.getenv("STP_DEFAULT_PRIORITY", "normal")
    
    # Require acknowledgment for critical packets
    STP_REQUIRE_ACK: bool = os.getenv("STP_REQUIRE_ACK", "false").lower() == "true"
    
    # ========================================================================
    # Karma Weighting Configuration (Phase 2.2)
    # ========================================================================
    
    # Karma Tracker endpoint URL
    KARMA_ENDPOINT: str = os.getenv(
        "KARMA_ENDPOINT",
        "http://localhost:8002/api/karma"
    )
    
    # Enable/disable Karma weighting
    KARMA_ENABLED: bool = os.getenv("KARMA_ENABLED", "true").lower() == "true"
    
    # Karma cache TTL (seconds)
    KARMA_CACHE_TTL: int = int(os.getenv("KARMA_CACHE_TTL", "60"))
    
    # Karma request timeout (seconds)
    KARMA_TIMEOUT: int = int(os.getenv("KARMA_TIMEOUT", "5"))
    
    # Karma weight in scoring (0-1)
    KARMA_WEIGHT: float = float(os.getenv("KARMA_WEIGHT", "0.15"))
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create global settings instance
settings = Settings()