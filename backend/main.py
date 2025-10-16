import logging, os, uuid, asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from uvicorn import Config

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
print(">>> main.py started")

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="Agentic RAG Chatbot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://agentic-rag-v0g1.onrender.com/"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Global variables
# -----------------------------
agents_initialized = False
coordinator = None

# -----------------------------
# Request / Response Models
# -----------------------------
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

# -----------------------------
# Lazy Agent Initialization
# -----------------------------
async def initialize_agents():
    """Initialize agents lazily on first request"""
    global agents_initialized, coordinator

    if agents_initialized:
        return

    try:
        # Import agents here to avoid blocking startup
        from agents.ingestion_agent import IngestionAgent
        from agents.retrieval_agent import RetrievalAgent
        from agents.llm_response_agent import LLMResponseAgent
        from agents.coordinator_agent import CoordinatorAgent
        from config import Config

        # Validate config (optional)
        try:
            Config.validate()
        except Exception as e:
            logger.warning(f"Config validation skipped/fails: {e}")

        # Ensure upload directory exists
        os.makedirs(Config.UPLOAD_DIRECTORY, exist_ok=True)

        # Initialize agents
        ingestion_agent = IngestionAgent()
        retrieval_agent = RetrievalAgent()
        llm_response_agent = LLMResponseAgent()
        coordinator = CoordinatorAgent()

        # Small delay to ensure setup
        await asyncio.sleep(0.1)
        agents_initialized = True
        logger.info("Agents initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent initialization failed: {str(e)}")

# -----------------------------
# API Endpoints
# -----------------------------
@app.get("/")
def root():
    return {"message": "Agentic RAG Chatbot API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_initialized": agents_initialized,
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    if not agents_initialized:
        await initialize_agents()

    try:
        upload_dir = os.environ.get("UPLOAD_DIR", "/tmp/uploads")
        os.makedirs(upload_dir, exist_ok=True)
        supported_extensions = {'.pdf', '.docx', '.pptx', '.csv', '.txt', '.md'}
        file_paths = []

        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in supported_extensions:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

            file_id = str(uuid.uuid4())
            file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")

            with open(file_path, "wb") as f:
                f.write(await file.read())

            file_paths.append(file_path)

        result = await coordinator.process_documents(
            file_paths, 
            [os.path.splitext(f)[1][1:] for f in file_paths]
        )
        return UploadResponse(**result)

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    if not agents_initialized:
        await initialize_agents()

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = await coordinator.answer_question(query=request.question, session_id=request.session_id)
        return QuestionResponse(**result)
    except Exception as e:
        logger.error(f"Question processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversation/{session_id}")
async def get_conversation_history(session_id: str):
    if not agents_initialized:
        await initialize_agents()
    return {"session_id": session_id, "history": coordinator.get_conversation_history(session_id)}

@app.delete("/conversation/{session_id}")
async def clear_conversation_history(session_id: str):
    if not agents_initialized:
        await initialize_agents()
    coordinator.clear_conversation_history(session_id)
    return {"message": f"Conversation history cleared for {session_id}"}
