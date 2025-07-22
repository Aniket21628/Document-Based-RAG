# Agentic RAG Chatbot

## Overview
The Agentic RAG Chatbot is a Retrieval-Augmented Generation (RAG) system designed to process and analyze documents, enabling users to upload files (PDF, DOCX, PPTX, CSV, TXT, Markdown) and ask questions based on their content. The system leverages a microservices-like architecture with specialized agents for document ingestion, retrieval, and response generation, powered by FastAPI for the backend and ReactJS for the frontend. It uses ChromaDB for vector storage and Google Gemini for natural language processing.

## Features
- **Document Processing**: Supports multiple file formats (PDF, DOCX, PPTX, CSV, TXT, Markdown) with dedicated parsers.
- **Vector Search**: Uses ChromaDB and sentence transformers for efficient similarity search.
- **Conversational AI**: Integrates Google Gemini for contextual question answering with conversation history.
- **Agent-Based Architecture**: Implements an MCP for communication between ingestion, retrieval, LLM response, and coordinator agents.
- **File Upload**: Allows users to upload documents up to 50MB via a ReactJS-based frontend.
- **RESTful API**: Provides endpoints for file uploads, question answering, and conversation history management.
- **CORS Support**: Configured for seamless integration with the ReactJS frontend running on `http://localhost:3000`.

## Project Structure
- **Backend**: Built with FastAPI, organized into agents and utilities.
  - `config.py`: Configuration settings for API keys, directories, and server parameters.
  - `mcp/`: For agent communication (`message_types.py`, `message_bus.py`).
  - `parsers/`: Document parsers for different file types (`pdf_parser.py`, `docx_parser.py`, `pptx_parser.py`, `csv_parser.py`, `txt_parser.py`).
  - `vector_store/`: ChromaDB integration for vector storage (`chroma_store.py`).
  - `agents/`: Agent implementations (`base_agent.py`, `ingestion_agent.py`, `retrieval_agent.py`, `llm_response_agent.py`, `coordinator_agent.py`).
  - `main.py`: FastAPI application with endpoints for health checks, file uploads, question answering, and conversation history.
- **Frontend**: Built with ReactJS, using libraries like `axios` for API calls, `react-dropzone` for file uploads, and `react-markdown` for rendering responses.
- **Dependencies**:
  - Backend: FastAPI, Uvicorn, ChromaDB, Google Generative AI, Sentence Transformers, PyPDF2, python-docx, python-pptx, pandas, and more (see `requirements.txt`).
  - Frontend: React, Tailwind CSS, Axios, React Dropzone, and testing libraries (see `package.json`).

## Prerequisites
- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **Google Gemini API Key**: Set as the `GEMINI_API_KEY` environment variable.
- **System Dependencies**: Ensure `libxml2` and `libxslt` are installed for `python-docx` and `python-pptx`.

## Installation

### Backend Setup
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd agentic-rag-chatbot
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Backend Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**:
   ```bash
   export GEMINI_API_KEY="your-gemini-api-key"  # On Windows: set GEMINI_API_KEY=your-gemini-api-key
   ```

5. **Run the Backend**:
   ```bash
   python main.py
   ```
   The FastAPI server will start on `http://0.0.0.0:8000`.

### Frontend Setup
1. **Navigate to the Frontend Directory**:
   ```bash
   cd frontend
   ```

2. **Install Frontend Dependencies**:
   ```bash
   npm install
   ```

3. **Run the Frontend**:
   ```bash
   npm run dev
   ```
   The ReactJS + Vite app will start on `http://localhost:5173`.

## Usage
1. **Upload Documents**:
   - Use the ReactJS frontend to upload supported document types (PDF, DOCX, PPTX, CSV, TXT, Markdown).
   - Alternatively, use the `/upload` endpoint via tools like Postman:
     ```bash
     curl -X POST -F "files=@document.pdf" http://localhost:8000/upload
     ```

2. **Ask Questions**:
   - Submit questions via the frontend or the `/ask` endpoint:
     ```bash
     curl -X POST -H "Content-Type: application/json" -d '{"question": "What is the main topic of the document?", "session_id": "user123"}' http://localhost:8000/ask
     ```

3. **Clear Conversation History**:
   - Clear history for a session using the `/conversation/{session_id}` DELETE endpoint:
     ```bash
     curl -X DELETE http://localhost:8000/conversation/user123
     ```

## API Endpoints
- **GET /**: Health check endpoint.
- **GET /health**: Detailed health status, including agent initialization and directory configurations.
- **POST /upload**: Upload and process documents (returns processed file list and status).
- **POST /ask**: Ask a question based on indexed documents (returns answer, sources, and confidence).
- **GET /conversation/{session_id}**: Retrieve conversation history for a session.
- **DELETE /conversation/{session_id}**: Clear conversation history for a session.

## Configuration
- **Backend**: Modify `config.py` to adjust settings like `CHROMA_PERSIST_DIRECTORY`, `UPLOAD_DIRECTORY`, `MAX_FILE_SIZE`, or `EMBEDDING_MODEL`.
- **Frontend**: Update `package.json` for additional dependencies or scripts, and configure CORS in `main.py` if the frontend URL changes.

## Development Notes
- **Logging**: Configured to provide detailed error and info logs for debugging.
- **Error Handling**: Comprehensive error handling in agents and API endpoints ensures robust operation.
- **Scalability**: The agent-based architecture and message bus allow for easy extension with additional agents or parsers.
- **Security**: Ensure the Gemini API key is securely stored and not exposed in version control.
