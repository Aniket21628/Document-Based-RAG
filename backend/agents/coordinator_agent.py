from agents.base_agent import BaseAgent
from mcp.message_types import (
    MCPMessage, MessageType, IngestionRequest, RetrievalRequest, LLMRequest
)
from mcp.message_bus import message_bus
from typing import List, Dict, Any, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CoordinatorAgent")
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        # Subscribe to STATUS messages to track processing updates
        self.subscribe_to_messages([MessageType.STATUS])
    
    async def process_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Process incoming messages - required by BaseAgent"""
        if message.type == MessageType.STATUS:
            # Handle status updates from other agents
            logger.info(f"Status update: {message.payload}")
            return None
        
        # CoordinatorAgent doesn't typically respond to messages directly
        # It orchestrates workflows programmatically
        return None
    
    async def process_documents(self, file_paths: List[str], file_types: List[str]) -> Dict[str, Any]:
        """Process uploaded documents through the agent pipeline"""
        trace_id = str(uuid.uuid4())
        
        try:
            # Step 1: Send to IngestionAgent
            ingestion_message = MCPMessage(
                trace_id=trace_id,
                sender=self.name,
                receiver="IngestionAgent",
                type=MessageType.INGESTION_REQUEST,
                payload=IngestionRequest(
                    file_paths=file_paths,
                    file_types=file_types
                ).dict()
            )
            
            ingestion_response = await message_bus.request_response(ingestion_message, timeout=60)
            
            if not ingestion_response.payload.get('success'):
                return {
                    'success': False,
                    'error': ingestion_response.payload.get('error_message', 'Document processing failed')
                }
            
            # Step 2: Send processed documents to RetrievalAgent for indexing
            retrieval_message = MCPMessage(
                trace_id=trace_id,
                sender=self.name,
                receiver="RetrievalAgent",
                type=MessageType.INGESTION_RESPONSE,
                payload=ingestion_response.payload
            )
            
            await message_bus.publish(retrieval_message)
            
            return {
                'success': True,
                'processed_files': ingestion_response.payload.get('processed_files', []),
                'message': 'Documents processed and indexed successfully'
            }
            
        except Exception as e:
            logger.error(f"Error processing documents: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def answer_question(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """Process user question through the RAG pipeline"""
        trace_id = str(uuid.uuid4())
        
        try:
            # Step 1: Retrieve relevant context
            retrieval_message = MCPMessage(
                trace_id=trace_id,
                sender=self.name,
                receiver="RetrievalAgent",
                type=MessageType.RETRIEVAL_REQUEST,
                payload=RetrievalRequest(
                    query=query,
                    top_k=5
                ).dict()
            )
            
            retrieval_response = await message_bus.request_response(retrieval_message, timeout=30)
            
            if retrieval_response.type == MessageType.ERROR:
                return {
                    'success': False,
                    'error': retrieval_response.payload.get('error', 'Retrieval failed')
                }
            
            # Step 2: Prepare context for LLM
            retrieved_chunks = retrieval_response.payload.get('retrieved_chunks', [])
            context = "\n\n".join([chunk['content'] for chunk in retrieved_chunks])
            
            # Get conversation history
            conversation_history = self.conversation_history.get(session_id, [])
            
            # Step 3: Generate response using LLM
            llm_message = MCPMessage(
                trace_id=trace_id,
                sender=self.name,
                receiver="LLMResponseAgent",
                type=MessageType.LLM_REQUEST,
                payload={
                    **LLMRequest(
                        query=query,
                        context=context,
                        conversation_history=conversation_history
                    ).dict(),
                    'retrieved_chunks': retrieved_chunks  # Pass for source extraction
                }
            )
            
            llm_response = await message_bus.request_response(llm_message, timeout=60)
            
            if llm_response.type == MessageType.ERROR:
                return {
                    'success': False,
                    'error': llm_response.payload.get('error', 'LLM generation failed')
                }
            
            # Update conversation history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            self.conversation_history[session_id].append({
                'user': query,
                'assistant': llm_response.payload['answer']
            })
            
            # Keep only last 10 turns
            if len(self.conversation_history[session_id]) > 10:
                self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
            
            return {
                'success': True,
                'answer': llm_response.payload['answer'],
                'sources': llm_response.payload.get('sources', []),
                'confidence': llm_response.payload.get('confidence', 0.0),
                'retrieved_chunks': retrieved_chunks
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        return self.conversation_history.get(session_id, [])
    
    def clear_conversation_history(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]