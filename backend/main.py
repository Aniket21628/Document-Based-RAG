from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import status as http_status
from pydantic import BaseModel
import shutil
import os
import uuid
import aiofiles
import logging
from pathlib import Path

from typing import Dict, Any
from agents.coordinator_agent import CoordinatorAgent
from agents.ingestion_agent import IngestionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.llm_response_agent import LLMResponseAgent
from models.schemas import QueryRequest, QueryResponse
from config import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Agentic RAG Chatbot", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agents
coordinator_agent = CoordinatorAgent()
ingestion_agent = IngestionAgent()
retrieval_agent = RetrievalAgent()
llm_response_agent = LLMResponseAgent()

class StatusResponse(BaseModel):
    status: str
    progress: float | None = None
    trace_id: str
    error: str | None = None

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    os.makedirs(Config.UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(Config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    
    await coordinator_agent.start()
    await ingestion_agent.start()
    await retrieval_agent.start()
    await llm_response_agent.start()
    
    logger.info("All agents started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await coordinator_agent.stop()
    await ingestion_agent.stop()
    await retrieval_agent.stop()
    await llm_response_agent.stop()
    logger.info("All agents stopped successfully")

# Initialize FastAPI without lifespan handler
app = FastAPI(title="Agentic RAG Chatbot", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload", tags=["File Upload"])
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and process a document asynchronously"""
    try:
        allowed_extensions = ['pdf', 'docx', 'pptx', 'csv', 'txt', 'md']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )

        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size too large. Maximum 50MB allowed."
            )
        
        safe_filename = Path(file.filename).name
        unique_filename = f"{uuid.uuid4().hex}_{safe_filename}"
        file_path = os.path.join(Config.UPLOAD_DIRECTORY, unique_filename)

        async with aiofiles.open(file_path, "wb") as out_file:
            await out_file.write(file_content)

        # 🔑 Generate a trace ID and pass it to the background task
        trace_id = uuid.uuid4().hex

        background_tasks.add_task(
            coordinator_agent.process_document_upload,
            file_path=file_path,
            file_name=unique_filename,
            file_type=file_extension,
            trace_id=trace_id
        )

        return JSONResponse(content={
            "message": "File uploaded; background processing started",
            "filename": unique_filename,
            "file_size": file_size,
            "trace_id": trace_id
        })

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", tags=["Query"])
async def query_documents(request: QueryRequest):
    """Query the uploaded documents"""
    try:
        result = await coordinator_agent.process_query(request.query)

        return JSONResponse(content={
            "message": "Query processing started",
            "trace_id": result["trace_id"],
            "query": request.query
        })

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{trace_id}", response_model=StatusResponse, tags=["Status"])
async def get_status(trace_id: str):
    """Get status of a request"""
    try:
        status_data = coordinator_agent.get_request_status(trace_id)
        
        if status_data is None:
            return StatusResponse(
                trace_id=trace_id,
                status="not_found",
                progress=None,
                error="No such trace ID found"
            )

        # Ensure the trace_id is included in the response
        return StatusResponse(trace_id=trace_id, **status_data)

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents": [
            "CoordinatorAgent",
            "IngestionAgent",
            "RetrievalAgent",
            "LLMResponseAgent"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
