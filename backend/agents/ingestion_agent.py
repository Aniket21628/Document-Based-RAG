import os
from typing import Dict, Any, List
from .base_agent import BaseAgent
from ..mcp.message_types import MCPMessage, MessageType
from ..services.document_parser import DocumentParser
from ..services.vector_store import ChromaVectorStore
import logging

logger = logging.getLogger(__name__)

class IngestionAgent(BaseAgent):
    def __init__(self):
        super().__init__("IngestionAgent")
        self.document_parser = DocumentParser()
        self.vector_store = ChromaVectorStore()
    
    async def handle_message(self, message: MCPMessage):
        """Handle ingestion requests"""
        if message.type == MessageType.INGESTION_REQUEST:
            await self._process_ingestion_request(message)
    
    async def _process_ingestion_request(self, message: MCPMessage):
        """Process document ingestion request"""
        try:
            file_path = message.payload.get('file_path')
            file_name = message.payload.get('file_name')
            file_type = message.payload.get('file_type')
            
            logger.info(f"Processing ingestion for {file_name}")
            
            # Parse document
            chunks = self.document_parser.parse_document(file_path, file_type)
            
            # Prepare metadata
            metadata = [
                {
                    'file_name': file_name,
                    'file_type': file_type,
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                }
                for i in range(len(chunks))
            ]
            
            # Add to vector store
            document_ids = self.vector_store.add_documents(chunks, metadata)
            
            # Send success response
            await self.send_message(
                receiver="CoordinatorAgent",
                message_type=MessageType.INGESTION_RESPONSE,
                payload={
                    'success': True,
                    'document_ids': document_ids,
                    'chunks_count': len(chunks),
                    'file_name': file_name
                },
                trace_id=message.trace_id
            )
            
        except Exception as e:
            logger.error(f"Error in ingestion: {e}")
            await self.send_message(
                receiver="CoordinatorAgent",
                message_type=MessageType.ERROR,
                payload={
                    'error': str(e),
                    'stage': 'ingestion'
                },
                trace_id=message.trace_id
            )