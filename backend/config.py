import os
from typing import Optional
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

class Config:
    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # ChromaDB Settings
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"
    
    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIRECTORY= os.environ.get("UPLOAD_DIR", "/tmp/uploads")
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # MCP Settings
    MCP_TIMEOUT: int = 30
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")

config = Config()