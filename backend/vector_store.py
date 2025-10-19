from urllib import response
import chromadb
from chromadb.config import Settings
import cohere
from typing import List, Dict, Any
import logging
import uuid
import shutil
import os
import time

logger = logging.getLogger(__name__)

class VectorStore:
    """Handle vector storage and retrieval with ChromaDB"""
    
    def __init__(self, persist_directory: str, collection_name: str, embedding_model: str):
        self.logger = logging.getLogger(__name__)

        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))
        self.embedding_model = embedding_model  # Keep for logging only
        
        # Initialize ChromaDB client with retry logic
        self.client = self._initialize_client()
        
        # Get or create collection with error handling
        self.collection = self._get_or_create_collection()
    
    def _initialize_client(self):
        """Initialize ChromaDB client with error handling"""
        try:
            client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB client initialized at: {self.persist_directory}")
            return client
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {str(e)}")
            raise
    
    def _get_or_create_collection(self):
        """Get or create collection with compatibility handling"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
            return collection
        except KeyError as e:
            # ChromaDB version incompatibility - reset and recreate
            logger.warning(f"Collection incompatible (KeyError: {str(e)}). Resetting ChromaDB...")
            return self._reset_and_create_collection()
        except ValueError as e:
            # Collection doesn't exist - create it
            logger.info(f"Collection doesn't exist. Creating: {self.collection_name}")
            return self._create_collection()
        except Exception as e:
            logger.error(f"Unexpected error accessing collection: {str(e)}")
            logger.warning("Attempting to reset ChromaDB...")
            return self._reset_and_create_collection()
    
    def _create_collection(self):
        """Create a new collection"""
        try:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")


    def _reset_and_create_collection(self):
        self.logger.warning(f"Deleting incompatible ChromaDB data at: {self.persist_directory}")
        import shutil, time

        for attempt in range(3):
            try:
                shutil.rmtree(self.persist_directory, ignore_errors=True)
                time.sleep(0.5)
                if not os.path.exists(self.persist_directory):
                    break
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1}: ChromaDB file busy, retrying in 1s...")
                time.sleep(1)
        else:
            # 🚨 Instead of crashing, just log and continue
            self.logger.warning(
                f"Skipping deletion — could not fully remove ChromaDB at {self.persist_directory}. "
                "It may be locked by another process."
            )

        os.makedirs(self.persist_directory, exist_ok=True)
        return self.client.create_collection(self.collection_name)
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def add_document(self, document: Dict[str, Any]):
        """Add a document to the vector store"""
        try:
            content = document.get('content', '')
            metadata = document.get('metadata', {})
            
            if not content.strip():
                logger.warning(f"Empty content for document: {metadata.get('file_path', 'unknown')}")
                return
            
            # Split into chunks
            chunks = self.chunk_text(content)
            
            if not chunks:
                logger.warning(f"No chunks created for document: {metadata.get('file_path', 'unknown')}")
                return
            
            chunk_ids = []
            chunk_texts = []
            chunk_embeddings = []
            chunk_metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_metadata = {
                    **metadata,
                    'chunk_index': i,
                    'chunk_count': len(chunks)
                }
                
                # Convert metadata values to strings (ChromaDB requirement)
                chunk_metadata = {k: str(v) for k, v in chunk_metadata.items()}
                
                # Generate embedding
                response = self.cohere_client.embed(
                    texts=[chunk],
                    model="embed-english-v3.0",
                    input_type="search_document"
                )
                embedding = response.embeddings[0]

                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                chunk_embeddings.append(embedding)
                chunk_metadatas.append(chunk_metadata)
            
            # Batch add to collection
            self.collection.add(
                documents=chunk_texts,
                embeddings=chunk_embeddings,
                metadatas=chunk_metadatas,
                ids=chunk_ids
            )
            
            logger.info(f"Added {len(chunks)} chunks from {metadata.get('file_path', 'unknown')}")
        
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            raise
    
    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search"""
        try:
            # Check if collection is empty
            count = self.collection.count()
            if count == 0:
                logger.warning("Collection is empty. No documents to search.")
                return []
            
            # Generate query embedding
            response = self.cohere_client.embed(
                texts=[query],
                model="embed-english-v3.0",
                input_type="search_query"
            )
            query_embedding = response.embeddings[0]

            # Adjust top_k if collection has fewer items
            actual_top_k = min(top_k, count)
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=actual_top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': 1 - results['distances'][0][i]
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant chunks for query")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'collection_name': self.collection_name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                'total_chunks': 0,
                'collection_name': self.collection_name,
                'error': str(e)
            }