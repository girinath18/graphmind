"""Testing configuration"""
import os
from app.core.config import Settings


class TestingSettings(Settings):
    """Testing environment settings"""
    
    debug: bool = True
    database_url: str = "sqlite:///:memory:"
    log_level: str = "DEBUG"
    
    class Config:
        env_file = ".env.testing"
