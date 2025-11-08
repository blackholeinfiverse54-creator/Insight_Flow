# app/core/database/__init__.py
from supabase import create_client, Client
from app.core.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client manager"""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client instance"""
        if cls._instance is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                raise ValueError("Supabase URL and Service Key must be configured")
            try:
                cls._instance = create_client(
                    supabase_url=settings.SUPABASE_URL,
                    supabase_key=settings.SUPABASE_SERVICE_KEY
                )
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                raise ConnectionError(f"Database connection failed: {e}") from e
        return cls._instance


# Initialize database client
def get_db() -> Client:
    """Dependency for getting database client"""
    return SupabaseClient.get_client()


# Database initialization scripts
async def init_database():
    """Initialize database tables and indexes"""
    db = get_db()
    
    # Note: These tables should be created via Supabase dashboard or migrations
    # This function can be used to verify tables exist
    
    tables_to_check = ["agents", "routing_logs", "performance_metrics", "feedback_events"]
    
    try:
        for table in tables_to_check:
            result = db.table(table).select("*", count="exact").limit(1).execute()
            logger.info(f"Table '{table}' verified - exists with {result.count} records")
    except Exception as e:
        logger.warning(f"Table verification warning: {e}")
        logger.info("Please ensure all required tables are created in Supabase")


__all__ = ['init_database', 'get_db', 'SupabaseClient']