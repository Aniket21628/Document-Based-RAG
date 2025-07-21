import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging
import uuid
import numpy as np

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    def __init__(self, persist_directory: str, collection_name: str, embedding_model: str):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(collection_name)
            logger.info(f"Created new collection: {collection_name}")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to the vector store"""
        all_chunks = []
        all_embeddings = []
        all_metadatas = []
        all_ids = []
        
        for doc in documents:
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # Split into chunks
            chunks = self.chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_metadata = {
                    **metadata,
                    'chunk_index': i,
                    'chunk_count': len(chunks)
                }
                
                all_chunks.append(chunk)
                all_metadatas.append(chunk_metadata)
                all_ids.append(chunk_id)
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(all_chunks).tolist()
        
        # Add to collection
        self.collection.add(
            documents=all_chunks,
            embeddings=embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )
        
        logger.info(f"Added {len(all_chunks)} chunks to vector store")
        return all_ids
    
    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'score': 1 - results['distances'][0][i]  # Convert distance to similarity
            })
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': self.collection_name
        }