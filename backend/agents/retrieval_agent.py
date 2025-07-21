from .base_agent import BaseAgent
from ..mcp.message_types import MCPMessage, MessageType
from ..services.vector_store import ChromaVectorStore
import logging

logger = logging.getLogger(__name__)

class RetrievalAgent(BaseAgent):
    def __init__(self):
        super().__init__("RetrievalAgent")
        self.vector_store = ChromaVectorStore()
    
    async def handle_message(self, message: MCPMessage):
        """Handle retrieval requests"""
        if message.type == MessageType.RETRIEVAL_REQUEST:
            await self._process_retrieval_request(message)
    
    async def _process_retrieval_request(self, message: MCPMessage):
        """Process document retrieval request"""
        try:
            query = message.payload.get('query')
            n_results = message.payload.get('n_results', 5)
            
            logger.info(f"Processing retrieval for query: {query}")
            
            # Search vector store
            search_results = self.vector_store.search(query, n_results)
            
            # Send results to LLM Response Agent
            await self.send_message(
                receiver="LLMResponseAgent",
                message_type=MessageType.RETRIEVAL_RESPONSE,
                payload={
                    'retrieved_context': search_results['documents'],
                    'metadatas': search_results['metadatas'],
                    'query': query,
                    'distances': search_results['distances']
                },
                trace_id=message.trace_id
            )
            
        except Exception as e:
            logger.error(f"Error in retrieval: {e}")
            await self.send_message(
                receiver="CoordinatorAgent",
                message_type=MessageType.ERROR,
                payload={
                    'error': str(e),
                    'stage': 'retrieval'
                },
                trace_id=message.trace_id
            )