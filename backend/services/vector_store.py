import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging
import uuid

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Document chunks for RAG"}
        )
    
    def add_documents(self, chunks: List[str], metadata: List[Dict[str, Any]]):
        """Add document chunks to the vector store"""
        try:
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks)
            
            # Generate unique IDs
            ids = [str(uuid.uuid4()) for _ in chunks]
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=chunks,
                metadatas=metadata,
                ids=ids
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def search(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results
            )
            
            return {
                'documents': results['documents'][0],
                'metadatas': results['metadatas'][0],
                'distances': results['distances'][0],
                'ids': results['ids'][0]
            }
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise
    
    def get_collection_count(self) -> int:
        """Get total number of documents in collection"""
        return self.collection.count()