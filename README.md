# Document Based RAG Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot system that enables intelligent Q&A over multiple document formats. Built with FastAPI, React, ChromaDB, and Google Gemini AI.

## 🌟 Features

- **Multi-Format Document Support**: Process PDF, DOCX, PPTX, CSV, TXT, Markdown, and Images (PNG/JPG/JPEG via Tesseract OCR)
- **Robust Security Guardrails**: 5-layer protection including prompt injection defense, SQL/Command injection blocking, toxicity filters, and real-time PII redaction.
- **Intelligent Vector Search**: ChromaDB with Cohere embeddings for semantic document retrieval
- **Conversational AI**: Google Gemini 2.0 Flash for contextual responses with conversation history
- **Modern UI**: React with TypeScript and Tailwind CSS for a sleek, responsive interface
- **Session Management**: Per-session conversation history tracking
- **Real-time Processing**: Instant document indexing and query responses
- **Source Attribution**: Transparent source citations for all responses

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: High-performance async web framework
- **ChromaDB**: Vector database for document embeddings
- **Cohere Embeddings**: `embed-english-v3.0` for semantic search
- **Google Gemini AI**: `gemini-2.0-flash-exp` for response generation
- **Python 3.8+**: Core backend runtime

### Frontend Stack
- **React 19**: Modern UI framework
- **TypeScript**: Type-safe development
- **Tailwind CSS 4**: Utility-first styling
- **Vite 7**: Lightning-fast build tool
- **Lucide React**: Beautiful icon system

### Key Components

```
backend/
├── main.py                 # FastAPI application & endpoints
├── config.py              # Configuration management
├── document_parser.py     # Multi-format document processors
├── vector_store.py        # ChromaDB integration
└── requirements.txt       # Python dependencies

frontend/
├── src/
│   ├── components/
│   │   └── RAGChatbot.tsx # Main chat interface
│   ├── App.tsx            # Root component
│   └── main.tsx           # Entry point
├── package.json           # Node dependencies
└── vite.config.ts         # Vite configuration
```

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **API Keys**:
  - Google Gemini API Key
  - Cohere API Key

### Backend Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Aniket21628/Document-Based-RAG.git
   cd agentic-rag-chatbot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**
   ```bash
   # Create .env file in backend directory
   echo "GEMINI_API_KEY=your-gemini-api-key" > .env
   echo "COHERE_API_KEY=your-cohere-api-key" >> .env
   ```

5. **Run Backend Server**
   ```bash
   uvicorn main:app --reload
   ```
   Server starts at `http://0.0.0.0:8000`

### Frontend Setup

1. **Navigate to Frontend Directory**
   ```bash
   cd frontend
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Configure API Endpoint** (optional)
   ```bash
   # Create .env file in frontend directory
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env
   ```

4. **Run Development Server**
   ```bash
   npm run dev
   ```
   Application starts at `http://localhost:5173`

## 📖 Usage

### Uploading Documents

1. Click the upload area or drag-and-drop files
2. Supported formats: PDF, DOCX, PPTX, CSV, TXT, MD, PNG, JPG, JPEG
3. Files are automatically processed and indexed
4. Maximum file size: 50MB per file

### Asking Questions

1. Type your question in the input field
2. Press Enter or click Send
3. Receive AI-generated responses with source citations
4. View confidence scores and relevant document sections


## 🔌 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Detailed health status |
| POST | `/upload` | Upload and process documents |
| POST | `/ask` | Ask questions with context |
| GET | `/conversation/{session_id}` | Get conversation history |
| DELETE | `/conversation/{session_id}` | Clear conversation history |

## ⚙️ Configuration

### Backend Configuration (`config.py`)

```python
GEMINI_API_KEY: str          # Required: Google Gemini API key
COHERE_API_KEY: str          # Required: Cohere API key
CHROMA_PERSIST_DIRECTORY: str # Vector DB storage path
UPLOAD_DIRECTORY: str         # Uploaded files directory
EMBEDDING_MODEL: str          # "embed-english-v3.0"
MAX_FILE_SIZE: int           # 50MB default
HOST: str                     # "0.0.0.0"
PORT: int                     # 8000
```

### Environment Variables

**Backend (.env)**
```env
GEMINI_API_KEY=your-gemini-api-key
COHERE_API_KEY=your-cohere-api-key
CHROMA_PERSIST_DIRECTORY=/tmp/chroma_db  # Optional
UPLOAD_DIR=/tmp/uploads                   # Optional
PORT=8000                                  # Optional
```

**Frontend (.env)**
```env
VITE_API_BASE_URL=http://localhost:8000
```


## 📝 Document Processing

### Supported Formats

| Format | Extension | Features |
|--------|-----------|----------|
| PDF | `.pdf` | Text extraction, page numbers |
| Word | `.docx` | Paragraphs, tables |
| PowerPoint | `.pptx` | Slides, shapes, tables |
| CSV | `.csv` | Headers, statistics, preview |
| Text | `.txt` | Plain text |
| Markdown | `.md` | Formatted text |
| Images | `.png`, `.jpg`, `.jpeg` | OCR Text extraction via Tesseract |

### Processing Pipeline

1. **File Upload**: Validated and saved temporarily
2. **Text Extraction**: Format-specific parsing
3. **Chunking**: Split into 1000-word chunks with 200-word overlap
4. **Embedding**: Generated using Cohere's `embed-english-v3.0`
5. **Storage**: Stored in ChromaDB with metadata
6. **Indexing**: Ready for semantic search

## 🚀 Deployment

### Render.com (Recommended)

Because this project uses Tesseract OCR for image processing, it requires system-level OS dependencies. The backend must be deployed using **Docker**.

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the **Environment** to `Docker`
4. Set the Docker Context / Dockerfile path to `./backend` (or `./backend/Dockerfile` depending on repo structure)
5. Add your environment variables (`GEMINI_API_KEY`, `COHERE_API_KEY`) in the Render dashboard
6. Deploy the frontend as a separate Static Site


Built with ❤️ using FastAPI, React, and AI