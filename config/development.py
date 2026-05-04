"""Development configuration"""
import os
from app.core.config import Settings


class DevelopmentSettings(Settings):
    """Development environment settings"""
    
    debug: bool = True
    database_url: str = os.getenv("DEV_DATABASE_URL", "sqlite:///./test.db")
    log_level: str = "DEBUG"
    
    class Config:
        env_file = ".env.development"
