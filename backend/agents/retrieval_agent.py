from agents.base_agent import BaseAgent
from mcp.message_types import MCPMessage, MessageType, RetrievalRequest, RetrievalResponse
from vector_store.chroma_store import ChromaVectorStore
from config import config
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RetrievalAgent(BaseAgent):
    def __init__(self):
        super().__init__("RetrievalAgent")
        self.vector_store = ChromaVectorStore(
            persist_directory=config.CHROMA_PERSIST_DIRECTORY,
            collection_name=config.CHROMA_COLLECTION_NAME,
            embedding_model=config.EMBEDDING_MODEL
        )
        self.subscribe_to_messages([MessageType.RETRIEVAL_REQUEST, MessageType.INGESTION_RESPONSE])
    
    async def process_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Process retrieval request or ingestion response"""
        if message.type == MessageType.RETRIEVAL_REQUEST:
            return await self.handle_retrieval_request(message)
        elif message.type == MessageType.INGESTION_RESPONSE:
            return await self.handle_ingestion_response(message)
        return None
    
    async def handle_ingestion_response(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle processed documents and add to vector store"""
        try:
            payload = message.payload
            if payload.get('success') and 'processed_documents' in payload:
                processed_documents = payload['processed_documents']
                
                # Add documents to vector store
                chunk_ids = self.vector_store.add_documents(processed_documents)
                logger.info(f"Added {len(chunk_ids)} chunks to vector store")
                
                # Update the response with chunk count
                payload['chunks_created'] = len(chunk_ids)
                
                return MCPMessage(
                    trace_id=message.trace_id,
                    sender=self.name,
                    receiver="CoordinatorAgent",
                    type=MessageType.STATUS,
                    payload={
                        'status': 'documents_indexed',
                        'chunks_created': len(chunk_ids)
                    }
                )
            
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
        
        return None
    
    async def handle_retrieval_request(self, message: MCPMessage) -> MCPMessage:
        """Handle similarity search request"""
        try:
            request_data = RetrievalRequest(**message.payload)
            
            # Perform similarity search
            results = self.vector_store.similarity_search(
                query=request_data.query,
                top_k=request_data.top_k
            )
            
            # Format response
            retrieved_chunks = []
            similarity_scores = []
            
            for result in results:
                retrieved_chunks.append({
                    'content': result['content'],
                    'metadata': result['metadata']
                })
                similarity_scores.append(result['score'])
            
            response = RetrievalResponse(
                retrieved_chunks=retrieved_chunks,
                similarity_scores=similarity_scores,
                query=request_data.query
            )
            
            return MCPMessage(
                trace_id=message.trace_id,
                sender=self.name,
                receiver=message.sender,
                type=MessageType.RETRIEVAL_RESPONSE,
                payload=response.dict()
            )
            
        except Exception as e:
            logger.error(f"Error in retrieval: {str(e)}")
            return MCPMessage(
                trace_id=message.trace_id,
                sender=self.name,
                receiver=message.sender,
                type=MessageType.ERROR,
                payload={'error': str(e)}
            )