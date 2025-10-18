import os
from typing import Optional
import dotenv

dotenv.load_dotenv()

class Config:
    # Google Gemini API
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    if os.name == "nt":  # Windows
        CHROMA_PERSIST_DIRECTORY = os.path.join(os.getcwd(), "chroma_db")
    else:
        CHROMA_PERSIST_DIRECTORY = "/opt/render/project/src/chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"
    
    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIRECTORY = os.getenv(
        "UPLOAD_DIR", 
        "/opt/render/project/src/uploads"
    )
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")

config = Config()