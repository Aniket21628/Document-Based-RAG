from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

class MessageType(Enum):
    # Ingestion Messages
    INGESTION_REQUEST = "INGESTION_REQUEST"
    INGESTION_RESPONSE = "INGESTION_RESPONSE"
    
    # Retrieval Messages
    RETRIEVAL_REQUEST = "RETRIEVAL_REQUEST"
    RETRIEVAL_RESPONSE = "RETRIEVAL_RESPONSE"
    
    # LLM Messages
    LLM_REQUEST = "LLM_REQUEST"
    LLM_RESPONSE = "LLM_RESPONSE"
    
    # System Messages
    ERROR = "ERROR"
    STATUS = "STATUS"

class MCPMessage(BaseModel):
    message_id: str = None
    trace_id: str
    sender: str
    receiver: str
    type: MessageType
    timestamp: datetime = None
    payload: Dict[str, Any]
    
    def __init__(self, **data):
        if not data.get('message_id'):
            data['message_id'] = str(uuid.uuid4())
        if not data.get('timestamp'):
            data['timestamp'] = datetime.now()
        super().__init__(**data)

class IngestionRequest(BaseModel):
    file_paths: List[str]
    file_types: List[str]

class IngestionResponse(BaseModel):
    success: bool
    processed_files: List[str]
    chunks_created: int
    error_message: Optional[str] = None

class RetrievalRequest(BaseModel):
    query: str
    top_k: int = 5

class RetrievalResponse(BaseModel):
    retrieved_chunks: List[Dict[str, Any]]
    similarity_scores: List[float]
    query: str

class LLMRequest(BaseModel):
    query: str
    context: str
    conversation_history: List[Dict[str, str]] = []

class LLMResponse(BaseModel):
    answer: str
    sources: List[str]
    confidence: Optional[float] = None