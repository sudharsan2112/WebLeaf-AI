"""
Configuration settings for the RAG-Powered Website Chatbot.
This file defines all the necessary configuration parameters including 
LLM models, embedding models, RAG chunking rules, and crawler limits.
"""
import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    """
    Settings model utilizing Pydantic for configuration validation.
    """
    # Application Configuration
    APP_NAME: str = "RAG Chatbot API (Groq)"
    APP_VERSION: str = "1.0.0"
    
    # API Provider Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = "groq/compound"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Generation Settings
    TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 1024
    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 3
    
    # Crawler Settings
    MAX_CRAWL_DEPTH: int = 3
    MAX_CRAWL_PAGES: int = 50
    RESPECT_ROBOTS_TXT: bool = True
    
    # Storage and File Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    DB_PATH: str = os.path.join(DATA_DIR, "chatbot.db")
    FAISS_INDEX_DIR: str = os.path.join(DATA_DIR, "faiss_store")
    
    # Supported Extensions to Ignore during crawling
    IGNORE_EXTENSIONS: set[str] = {
        ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".mp4", 
        ".avi", ".mov", ".css", ".js", ".zip", ".tar", ".gz", ".xml"
    }

    def setup_directories(self) -> None:
        """
        Creates necessary data storage directories if they do not exist.
        This ensures that SQLite and FAISS have valid paths to write to.
        """
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.FAISS_INDEX_DIR, exist_ok=True)


# Instantiate a global settings object for use across the application
settings = Settings()

# Immediately setup required directories upon initialization
settings.setup_directories()
