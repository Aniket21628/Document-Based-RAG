from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    sources: List[Dict[str, Any]]
    trace_id: str

class UploadResponse(BaseModel):
    message: str
    trace_id: str
    filename: str
    file_size: int

class StatusResponse(BaseModel):
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None