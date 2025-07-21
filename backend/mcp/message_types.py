from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

class MessageType(Enum):
    INGESTION_REQUEST = "INGESTION_REQUEST"
    INGESTION_RESPONSE = "INGESTION_RESPONSE"
    RETRIEVAL_REQUEST = "RETRIEVAL_REQUEST"
    RETRIEVAL_RESPONSE = "RETRIEVAL_RESPONSE"
    LLM_REQUEST = "LLM_REQUEST"
    LLM_RESPONSE = "LLM_RESPONSE"
    ERROR = "ERROR"

class MCPMessage(BaseModel):
    sender: str
    receiver: str
    type: MessageType
    trace_id: str
    timestamp: datetime
    payload: Dict[str, Any]
    
    @classmethod
    def create(cls, sender: str, receiver: str, message_type: MessageType, 
               payload: Dict[str, Any], trace_id: Optional[str] = None):
        return cls(
            sender=sender,
            receiver=receiver,
            type=message_type,
            trace_id=trace_id or str(uuid.uuid4()),
            timestamp=datetime.now(),
            payload=payload
        )