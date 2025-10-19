import logging
import os
import uuid
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from config import config
from document_parser import DocumentProcessor
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Simple RAG Chatbot", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://agentic-rag-v0g1.onrender.com",
        "https://agentic-rag-backend-1w20.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
vector_store: Optional[VectorStore] = None
doc_processor: Optional[DocumentProcessor] = None
conversation_history: Dict[str, List[Dict[str, str]]] = {}
gemini_model = None

# Pydantic models
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

def initialize_services():
    """Initialize services on startup"""
    global vector_store, doc_processor, gemini_model
    
    try:
        logger.info("Initializing services...")
        
        # Validate config
        config.validate()
        
        # Create directories
        os.makedirs(config.UPLOAD_DIRECTORY, exist_ok=True)
        os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        
        # Initialize Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Initialize vector store
        vector_store = VectorStore(
            persist_directory=config.CHROMA_PERSIST_DIRECTORY,
            collection_name=config.CHROMA_COLLECTION_NAME,
            embedding_model=config.EMBEDDING_MODEL
        )
        
        # Initialize document processor
        doc_processor = DocumentProcessor()
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise

@app.on_event("startup")
async def startup_event():
    """Run initialization on startup"""
    initialize_services()

@app.get("/")
def root():
    return {"message": "Simple RAG Chatbot API is running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "services": {
            "vector_store": vector_store is not None,
            "doc_processor": doc_processor is not None,
            "gemini": gemini_model is not None
        }
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    logger.info(f"Received upload request with {len(files)} files")
    
    try:
        supported_extensions = {'.pdf', '.docx', '.pptx', '.csv', '.txt', '.md'}
        file_paths = []
        processed_files = []

        # Save files
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in supported_extensions:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

            file_id = str(uuid.uuid4())
            file_path = os.path.join(config.UPLOAD_DIRECTORY, f"{file_id}_{file.filename}")
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            file_paths.append(file_path)
            logger.info(f"Saved file: {file.filename}")

        # Process documents
        for file_path in file_paths:
            try:
                document = doc_processor.process_file(file_path)
                vector_store.add_document(document)
                processed_files.append(os.path.basename(file_path))
                logger.info(f"Processed and indexed: {os.path.basename(file_path)}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue

        return UploadResponse(
            success=True,
            processed_files=processed_files,
            message=f"Successfully processed {len(processed_files)} file(s)"
        )

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return UploadResponse(
            success=False,
            error=str(e)
        )

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question based on uploaded documents"""
    logger.info(f"Received question: {request.question}")
    
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        # Retrieve relevant documents
        results = vector_store.similarity_search(request.question, top_k=5)
        
        if not results:
            return QuestionResponse(
                success=True,
                answer="I don't have enough information to answer that question. Please upload relevant documents first.",
                sources=[],
                confidence=0.0
            )

        # Prepare context
        context = "\n\n".join([r['content'] for r in results])
        
        # Get conversation history
        history = conversation_history.get(request.session_id, [])
        
        # Create prompt
        prompt = create_prompt(request.question, context, history)
        
        # Generate answer
        response = gemini_model.generate_content(prompt)
        answer = response.text
        
        # Extract sources
        sources = []
        for result in results:
            metadata = result.get('metadata', {})
            file_path = metadata.get('file_path', 'Unknown')
            filename = os.path.basename(file_path)
            file_type = metadata.get('file_type', 'Unknown')
            source = f"{filename} ({file_type})"
            if source not in sources:
                sources.append(source)
        
        # Calculate confidence
        confidence = min(0.9, len(context) / 2000)
        
        # Update conversation history
        if request.session_id not in conversation_history:
            conversation_history[request.session_id] = []
        
        conversation_history[request.session_id].append({
            'user': request.question,
            'assistant': answer
        })
        
        # Keep only last 10 turns
        if len(conversation_history[request.session_id]) > 10:
            conversation_history[request.session_id] = conversation_history[request.session_id][-10:]
        
        return QuestionResponse(
            success=True,
            answer=answer,
            sources=sources,
            confidence=confidence
        )

    except Exception as e:
        logger.error(f"Question processing error: {str(e)}", exc_info=True)
        return QuestionResponse(
            success=False,
            error=str(e)
        )

@app.get("/conversation/{session_id}")
def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    return {
        "session_id": session_id,
        "history": conversation_history.get(session_id, [])
    }

@app.delete("/conversation/{session_id}")
def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    if session_id in conversation_history:
        del conversation_history[session_id]
    return {"message": f"Conversation history cleared for {session_id}"}

def create_prompt(query: str, context: str, history: List[Dict[str, str]]) -> str:
    """Create a prompt for Gemini"""
    history_text = ""
    if history:
        history_text = "\n\nPrevious Conversation:\n"
        for turn in history[-3:]:
            history_text += f"User: {turn.get('user', '')}\n"
            history_text += f"Assistant: {turn.get('assistant', '')}\n"
    
    prompt = f"""You are a helpful AI assistant that answers questions based on provided document context.

CONTEXT FROM DOCUMENTS:
{context}

{history_text}

CURRENT QUESTION: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, clearly state what information is missing. Always cite which parts of the context you're using to support your answer.

Rules:
1. Base your answer primarily on the provided context
2. Be specific and detailed in your response
3. If you mention specific data or facts, indicate which document/source it came from
4. If the context is insufficient, clearly state what additional information would be needed
5. Maintain a helpful and professional tone

Answer:"""
    
    return prompt

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT)