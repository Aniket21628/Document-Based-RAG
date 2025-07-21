from .base_agent import BaseAgent
from ..mcp.message_types import MCPMessage, MessageType
from ..services.gemini_client import GeminiClient
import logging

logger = logging.getLogger(__name__)

class LLMResponseAgent(BaseAgent):
    def __init__(self):
        super().__init__("LLMResponseAgent")
        self.gemini_client = GeminiClient()
    
    async def handle_message(self, message: MCPMessage):
        """Handle LLM response requests"""
        if message.type == MessageType.RETRIEVAL_RESPONSE:
            await self._process_llm_request(message)
    
    async def _process_llm_request(self, message: MCPMessage):
        """Process LLM response generation"""
        try:
            query = message.payload.get('query')
            retrieved_context = message.payload.get('retrieved_context', [])
            metadatas = message.payload.get('metadatas', [])
            
            logger.info(f"Generating LLM response for query: {query}")
            
            # Generate response using Gemini
            response = await self.gemini_client.generate_response(
                query=query,
                context_chunks=retrieved_context
            )
            
            # Prepare source information
            sources = []
            for i, metadata in enumerate(metadatas):
                if i < len(retrieved_context):
                    sources.append({
                        'file_name': metadata.get('file_name', 'Unknown'),
                        'chunk_id': metadata.get('chunk_id', i),
                        'content_preview': retrieved_context[i][:200] + "..."
                    })
            
            # Send response back to coordinator
            await self.send_message(
                receiver="CoordinatorAgent",
                message_type=MessageType.LLM_RESPONSE,
                payload={
                    'response': response,
                    'sources': sources,
                    'query': query
                },
                trace_id=message.trace_id
            )
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            await self.send_message(
                receiver="CoordinatorAgent",
                message_type=MessageType.ERROR,
                payload={
                    'error': str(e),
                    'stage': 'llm_response'
                },
                trace_id=message.trace_id
            )