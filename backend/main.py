from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
import os
import asyncio
from typing import Dict, Any
import logging

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
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agents
coordinator_agent = CoordinatorAgent()
ingestion_agent = IngestionAgent()
retrieval_agent = RetrievalAgent()
llm_response_agent = LLMResponseAgent()

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    os.makedirs(Config.UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(Config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    
    # Start all agents
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

@app.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Validate file type
        allowed_extensions = ['pdf', 'docx', 'pptx', 'csv', 'txt', 'md']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Check file size
        file_size = 0
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="File size too large. Maximum 50MB allowed."
            )
        
        # Save file
        file_path = os.path.join(Config.UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Process with coordinator agent
        result = await coordinator_agent.process_document_upload(
            file_path=file_path,
            file_name=file.filename,
            file_type=file_extension
        )
        
        return JSONResponse(content={
            "message": "File uploaded and processing started",
            "trace_id": result["trace_id"],
            "filename": file.filename,
            "file_size": file_size
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
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

@app.get("/status/{trace_id}")
async def get_status(trace_id: str):
    """Get status of a request"""
    try:
        status = coordinator_agent.get_request_status(trace_id)
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agents": ["CoordinatorAgent", "IngestionAgent", "RetrievalAgent", "LLMResponseAgent"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)