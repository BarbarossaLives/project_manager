#!/usr/bin/env python3
"""
Enhanced startup script for Project Manager
Handles automatic setup of database, AI, and server startup
"""

import os
import sys
import subprocess
import time
import logging
import requests
from pathlib import Path

# Add the project directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectManagerStarter:
    def __init__(self):
        self.config = config
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        logger.info("🔍 Checking dependencies...")
        
        try:
            import fastapi
            import sqlalchemy
            import uvicorn
            logger.info("✅ Core dependencies found")
            return True
        except ImportError as e:
            logger.error(f"❌ Missing dependency: {e}")
            logger.info("💡 Run: pip install -r requirements.txt")
            return False
    
    def setup_database(self):
        """Initialize database tables"""
        if not self.config.AUTO_SETUP_DATABASE:
            logger.info("⏭️  Database auto-setup disabled")
            return True

        logger.info("🗄️  Setting up database...")

        try:
            from backend.database import engine
            from backend.models import models

            # Create all tables
            models.Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created/verified")

            # Check if migration is needed
            self._check_and_migrate_database()

            return True

        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False

    def _check_and_migrate_database(self):
        """Check if database migration is needed and run it"""
        try:
            import sqlite3
            from pathlib import Path

            # Get database path
            db_url = self.config.DATABASE_URL
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")

                if Path(db_path).exists():
                    # Check if tasks table has description column
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA table_info(tasks)")
                    columns = [row[1] for row in cursor.fetchall()]
                    conn.close()

                    if "description" not in columns:
                        logger.info("🔄 Database migration needed...")
                        # Run migration
                        import subprocess
                        result = subprocess.run(
                            ["python", "migrate_database.py"],
                            capture_output=True,
                            text=True,
                            cwd=Path(__file__).parent
                        )

                        if result.returncode == 0:
                            logger.info("✅ Database migration completed")
                        else:
                            logger.warning(f"⚠️  Migration warning: {result.stderr}")
                    else:
                        logger.info("✅ Database schema is up to date")

        except Exception as e:
            logger.warning(f"⚠️  Could not check database migration: {e}")
    
    def check_ollama_installed(self):
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def check_ollama_running(self):
        """Check if Ollama service is running"""
        try:
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_ollama_service(self):
        """Start Ollama service if not running"""
        if not self.config.AUTO_START_OLLAMA:
            logger.info("⏭️  Ollama auto-start disabled")
            return True
            
        if self.check_ollama_running():
            logger.info("✅ Ollama service already running")
            return True
            
        if not self.check_ollama_installed():
            logger.warning("⚠️  Ollama not installed. AI features will be disabled.")
            logger.info("💡 Run: python setup_ollama.py to install Ollama")
            return False
            
        logger.info("🚀 Starting Ollama service...")
        
        try:
            # Start Ollama in background
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait for service to start
            for i in range(30):
                if self.check_ollama_running():
                    logger.info("✅ Ollama service started")
                    return True
                time.sleep(1)
                if i % 5 == 0:
                    logger.info(f"⏳ Waiting for Ollama... ({i+1}/30)")
            
            logger.warning("⚠️  Ollama service didn't start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start Ollama: {e}")
            return False
    
    def check_ollama_model(self):
        """Check if the required model is available"""
        if not self.check_ollama_running():
            return False
            
        try:
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                # Check if our model is available
                for model_name in model_names:
                    if self.config.OLLAMA_MODEL in model_name:
                        logger.info(f"✅ Model {self.config.OLLAMA_MODEL} is available")
                        return True
                
                logger.warning(f"⚠️  Model {self.config.OLLAMA_MODEL} not found")
                logger.info(f"💡 Available models: {', '.join(model_names)}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to check models: {e}")
            return False
    
    def setup_ai(self):
        """Setup AI components"""
        if not self.config.AUTO_SETUP_AI:
            logger.info("⏭️  AI auto-setup disabled")
            return True
            
        logger.info("🤖 Setting up AI components...")
        
        # Start Ollama service
        if not self.start_ollama_service():
            logger.warning("⚠️  AI features will be limited without Ollama")
            return False
        
        # Check model availability
        if not self.check_ollama_model():
            logger.info(f"📥 Pulling {self.config.OLLAMA_MODEL} model...")
            try:
                result = subprocess.run(['ollama', 'pull', self.config.OLLAMA_MODEL], 
                                      timeout=300, check=True)
                logger.info(f"✅ Model {self.config.OLLAMA_MODEL} downloaded")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.error(f"❌ Failed to download model: {e}")
                return False
        
        return True
    
    def create_directories(self):
        """Create necessary directories"""
        logger.info("📁 Creating directories...")
        
        directories = [
            self.config.UPLOAD_DIR,
            self.config.STATIC_DIR,
            self.config.TEMPLATES_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.info("✅ Directories created/verified")
    
    def start_server(self):
        """Start the FastAPI server"""
        logger.info(f"🚀 Starting Project Manager on {self.config.get_server_url()}")
        
        try:
            import uvicorn
            
            # Start the server
            uvicorn.run(
                "backend.main:app",
                host=self.config.HOST,
                port=self.config.PORT,
                reload=self.config.RELOAD,
                log_level=self.config.LOG_LEVEL.lower()
            )
            
        except KeyboardInterrupt:
            logger.info("👋 Server stopped by user")
        except Exception as e:
            logger.error(f"❌ Server failed to start: {e}")
            return False
        
        return True
    
    def run(self):
        """Main startup sequence"""
        print("🚀 Project Manager Startup")
        print("=" * 50)
        
        # Print configuration
        self.config.print_config()
        print()
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Create directories
        self.create_directories()
        
        # Setup database
        if not self.setup_database():
            logger.error("❌ Database setup failed")
            return False
        
        # Setup AI
        ai_ready = self.setup_ai()
        if not ai_ready:
            logger.warning("⚠️  Continuing without full AI capabilities")
        
        print("\n🎉 Setup completed!")
        print(f"🌐 Access your Project Manager at: {self.config.get_server_url()}")
        
        if ai_ready:
            print("🤖 AI features are ready!")
        else:
            print("⚠️  AI features limited - run 'python setup_ollama.py' for full AI support")
        
        print("\n" + "=" * 50)
        
        # Start server
        return self.start_server()

def main():
    """Entry point"""
    try:
        starter = ProjectManagerStarter()
        success = starter.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Startup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
