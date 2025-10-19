import os
from typing import Optional
import dotenv

dotenv.load_dotenv()

class Config:
    # === API Keys ===
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    COHERE_API_KEY: Optional[str] = os.getenv("COHERE_API_KEY")
    
    # === Directories ===
    if os.name == "nt":  # Windows
        CHROMA_PERSIST_DIRECTORY = os.path.join(os.getcwd(), "chroma_db")
    else:
        CHROMA_PERSIST_DIRECTORY = "/opt/render/project/src/chroma_db"
    
    CHROMA_COLLECTION_NAME: str = "documents"
    UPLOAD_DIRECTORY: str = os.getenv("UPLOAD_DIR", "/opt/render/project/src/uploads")

    # === Embeddings ===
    EMBEDDING_MODEL: str = "embed-english-v3.0"

    # === File Settings ===
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

    # === Server Settings ===
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))

    @classmethod
    def validate(cls):
        """Ensure all required environment variables are present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("❌ GEMINI_API_KEY environment variable is required.")
        if not cls.COHERE_API_KEY:
            raise ValueError("❌ COHERE_API_KEY environment variable is required for embeddings.")

config = Config()
