"""Production configuration"""
import os
from app.core.config import Settings


class ProductionSettings(Settings):
    """Production environment settings"""
    
    debug: bool = False
    database_url: str = os.getenv("DATABASE_URL")
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env.production"
