from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
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

# Global agents
coordinator_agent = CoordinatorAgent()
ingestion_agent = IngestionAgent()
retrieval_agent = RetrievalAgent()
llm_response_agent = LLMResponseAgent()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context: replaces startup/shutdown events"""
    os.makedirs(Config.UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(Config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

    await coordinator_agent.start()
    await ingestion_agent.start()
    await retrieval_agent.start()
    await llm_response_agent.start()
    logger.info("All agents started successfully")

    yield  # App is running

    await coordinator_agent.stop()
    await ingestion_agent.stop()
    await retrieval_agent.stop()
    await llm_response_agent.stop()
    logger.info("All agents stopped successfully")

# Initialize FastAPI with lifespan handler
app = FastAPI(title="Agentic RAG Chatbot", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        allowed_extensions = ['pdf', 'docx', 'pptx', 'csv', 'txt', 'md']
        file_extension = file.filename.split('.')[-1].lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}")

        file_content = await file.read()
        file_size = len(file_content)

        if file_size > Config.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size too large. Maximum 50MB allowed.")

        file_path = os.path.join(Config.UPLOAD_DIRECTORY, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

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
    try:
        status = coordinator_agent.get_request_status(trace_id)
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agents": ["CoordinatorAgent", "IngestionAgent", "RetrievalAgent", "LLMResponseAgent"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
