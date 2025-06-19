# config.py - Configuration settings for Project Manager
import os
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip loading .env file
    pass

class Config:
    # Server Configuration
    HOST = os.getenv("PROJECT_MANAGER_HOST", "0.0.0.0")
    PORT = int(os.getenv("PROJECT_MANAGER_PORT", "8080"))  # Changed from 8000 to 8080
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./project_tracker.db")
    
    # AI Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    # Auto-setup Configuration
    AUTO_SETUP_DATABASE = os.getenv("AUTO_SETUP_DATABASE", "true").lower() == "true"
    AUTO_SETUP_AI = os.getenv("AUTO_SETUP_AI", "true").lower() == "true"
    AUTO_START_OLLAMA = os.getenv("AUTO_START_OLLAMA", "true").lower() == "true"
    
    # File Paths
    BASE_DIR = Path(__file__).parent
    UPLOAD_DIR = BASE_DIR / "uploads"
    STATIC_DIR = BASE_DIR / "frontend" / "static"
    TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Development Configuration
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD = os.getenv("RELOAD", "true").lower() == "true"
    
    @classmethod
    def get_server_url(cls):
        """Get the full server URL"""
        return f"http://{cls.HOST}:{cls.PORT}"
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("🔧 Project Manager Configuration:")
        print(f"   Server: {cls.get_server_url()}")
        print(f"   Database: {cls.DATABASE_URL}")
        print(f"   Ollama: {cls.OLLAMA_BASE_URL}")
        print(f"   Model: {cls.OLLAMA_MODEL}")
        print(f"   Auto-setup: DB={cls.AUTO_SETUP_DATABASE}, AI={cls.AUTO_SETUP_AI}")
        print(f"   Debug: {cls.DEBUG}")

# Environment-specific configurations
class DevelopmentConfig(Config):
    DEBUG = True
    RELOAD = True

class ProductionConfig(Config):
    DEBUG = False
    RELOAD = False
    LOG_LEVEL = "WARNING"

class TestingConfig(Config):
    DATABASE_URL = "sqlite:///./test_project_tracker.db"
    AUTO_SETUP_AI = False

# Select configuration based on environment
ENV = os.getenv("ENVIRONMENT", "development").lower()

if ENV == "production":
    config = ProductionConfig()
elif ENV == "testing":
    config = TestingConfig()
else:
    config = DevelopmentConfig()
