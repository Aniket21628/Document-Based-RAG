import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    CHROMA_PERSIST_DIRECTORY = "./chroma_db"
    UPLOAD_DIRECTORY = "./uploads"
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # MCP Configuration
    MCP_TIMEOUT = 30
    MAX_RETRIES = 3