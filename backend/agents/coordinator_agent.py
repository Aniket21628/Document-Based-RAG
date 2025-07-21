import asyncio
from typing import Dict, Any
from .base_agent import BaseAgent
from ..mcp.message_types import MCPMessage, MessageType
import logging

logger = logging.getLogger(__name__)

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CoordinatorAgent")
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
    
    async def handle_message(self, message: MCPMessage):
        """Handle coordination messages"""
        if message.type == MessageType.INGESTION_RESPONSE:
            await self._handle_ingestion_response(message)
        elif message.type == MessageType.LLM_RESPONSE:
            await self._handle_llm_response(message)
        elif message.type == MessageType.ERROR:
            await self._handle_error_response(message)
    
    async def process_document_upload(self, file_path: str, file_name: str, file_type: str) -> Dict[str, Any]:
        """Coordinate document upload process"""
        trace_id = f"upload_{file_name}_{asyncio.get_event_loop().time()}"
        
        # Store request info
        self.pending_requests[trace_id] = {
            'type': 'upload',
            'status': 'processing',
            'file_name': file_name
        }
        
        # Send to ingestion agent
        await self.send_message(
            receiver="IngestionAgent",
            message_type=MessageType.INGESTION_REQUEST,
            payload={
                'file_path': file_path,
                'file_name': file_name,
                'file_type': file_type
            },
            trace_id=trace_id
        )
        
        return {'trace_id': trace_id, 'status': 'processing'}
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Coordinate query processing"""
        trace_id = f"query_{asyncio.get_event_loop().time()}"
        
        # Store request info
        self.pending_requests[trace_id] = {
            'type': 'query',
            'status': 'processing',
            'query': query
        }
        
        # Send to retrieval agent
        await self.send_message(
            receiver="RetrievalAgent",
            message_type=MessageType.RETRIEVAL_REQUEST,
            payload={
                'query': query,
                'n_results': 5
            },
            trace_id=trace_id
        )
        
        return {'trace_id': trace_id, 'status': 'processing'}
    
    async def _handle_ingestion_response(self, message: MCPMessage):
        """Handle ingestion completion"""
        trace_id = message.trace_id
        if trace_id in self.pending_requests:
            self.pending_requests[trace_id].update({
                'status': 'completed',
                'result': message.payload
            })
    
    async def _handle_llm_response(self, message: MCPMessage):
        """Handle LLM response completion"""
        trace_id = message.trace_id
        if trace_id in self.pending_requests:
            self.pending_requests[trace_id].update({
                'status': 'completed',
                'result': message.payload
            })
    
    async def _handle_error_response(self, message: MCPMessage):
        """Handle error responses"""
        trace_id = message.trace_id
        if trace_id in self.pending_requests:
            self.pending_requests[trace_id].update({
                'status': 'error',
                'error': message.payload.get('error')
            })
    
    def get_request_status(self, trace_id: str) -> Dict[str, Any]:
        """Get status of a request"""
        return self.pending_requests.get(trace_id, {'status': 'not_found'})