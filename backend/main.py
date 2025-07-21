from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import uuid
import asyncio
import logging

# Import agents
from agents.ingestion_agent import IngestionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.llm_response_agent import LLMResponseAgent
from agents.coordinator_agent import CoordinatorAgent
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Agentic RAG Chatbot", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
agents_initialized = False
coordinator = None

# Request/Response Models
class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"

class QuestionResponse(BaseModel):
    success: bool
    answer: Optional[str] = None
    sources: List[str] = []
    confidence: Optional[float] = None
    error: Optional[str] = None

class UploadResponse(BaseModel):
    success: bool
    processed_files: List[str] = []
    message: Optional[str] = None
    error: Optional[str] = None

# Initialize agents
async def initialize_agents():
    """Initialize all agents"""
    global agents_initialized, coordinator
    
    if agents_initialized:
        return
    
    try:
        # Validate configuration
        Config.validate()
        
        # Create upload directory
        os.makedirs(Config.UPLOAD_DIRECTORY, exist_ok=True)
        
        # Initialize agents
        ingestion_agent = IngestionAgent()
        retrieval_agent = RetrievalAgent()
        llm_response_agent = LLMResponseAgent()
        coordinator = CoordinatorAgent()
        
        # Small delay to ensure all subscriptions are set up
        await asyncio.sleep(0.1)
        
        agents_initialized = True
        logger.info("All agents initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent initialization failed: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    await initialize_agents()

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Agentic RAG Chatbot API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "agents_initialized": agents_initialized,
        "upload_directory": Config.UPLOAD_DIRECTORY,
        "chroma_directory": Config.CHROMA_PERSIST_DIRECTORY
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    if not agents_initialized:
        await initialize_agents()
    
    try:
        # Validate file types
        supported_extensions = {'.pdf', '.docx', '.pptx', '.csv', '.txt', '.md'}
        file_paths = []
        file_types = []
        
        for file in files:
            if not file.filename:
                continue
                
            # Check file extension
            file_extension = os.path.splitext(file.filename.lower())[1]
            if file_extension not in supported_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_extension}"
                )
            
            # Save uploaded file
            file_id = str(uuid.uuid4())
            file_path = os.path.join(Config.UPLOAD_DIRECTORY, f"{file_id}_{file.filename}")
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_paths.append(file_path)
            file_types.append(file_extension.lstrip('.'))
        
        if not file_paths:
            raise HTTPException(status_code=400, detail="No valid files uploaded")
        
        # Process documents through coordinator
        result = await coordinator.process_documents(file_paths, file_types)
        
        return UploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question to the RAG system"""
    if not agents_initialized:
        await initialize_agents()
    
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Process question through coordinator
        result = await coordinator.answer_question(
            query=request.question,
            session_id=request.session_id
        )
        
        return QuestionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    if not agents_initialized:
        await initialize_agents()
    
    try:
        history = coordinator.get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversation/{session_id}")
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    if not agents_initialized:
        await initialize_agents()
    
    try:
        coordinator.clear_conversation_history(session_id)
        return {"message": f"Conversation history cleared for session {session_id}"}
    except Exception as e:
        logger.error(f"Error clearing conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)