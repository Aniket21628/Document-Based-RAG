import os
from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent
from mcp.message_types import MCPMessage, MessageType, IngestionRequest, IngestionResponse
from parsers.pdf_parser import PDFParser
from parsers.docx_parser import DOCXParser
from parsers.pptx_parser import PPTXParser
from parsers.csv_parser import CSVParser
from parsers.txt_parser import TXTParser
import logging

logger = logging.getLogger(__name__)

class IngestionAgent(BaseAgent):
    def __init__(self):
        super().__init__("IngestionAgent")
        self.parsers = {
            'pdf': PDFParser(),
            'docx': DOCXParser(),
            'pptx': PPTXParser(),
            'csv': CSVParser(),
            'txt': TXTParser(),
            'md': TXTParser(),
            'markdown': TXTParser()
        }
        self.subscribe_to_messages([MessageType.INGESTION_REQUEST])
    
    async def process_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Process ingestion request"""
        if message.type == MessageType.INGESTION_REQUEST:
            return await self.handle_ingestion_request(message)
        return None
    
    async def handle_ingestion_request(self, message: MCPMessage) -> MCPMessage:
        """Handle document ingestion request"""
        try:
            request_data = IngestionRequest(**message.payload)
            processed_documents = []
            
            for file_path, file_type in zip(request_data.file_paths, request_data.file_types):
                if not os.path.exists(file_path):
                    logger.error(f"File not found: {file_path}")
                    continue
                
                parser = self.parsers.get(file_type.lower())
                if not parser:
                    logger.error(f"No parser available for file type: {file_type}")
                    continue
                
                try:
                    parsed_doc = parser.parse(file_path)
                    processed_documents.append(parsed_doc)
                    logger.info(f"Successfully parsed {file_path}")
                except Exception as e:
                    logger.error(f"Error parsing {file_path}: {str(e)}")
            
            response = IngestionResponse(
                success=len(processed_documents) > 0,
                processed_files=[doc['metadata']['file_path'] for doc in processed_documents],
                chunks_created=0  # Will be updated after vector store processing
            )
            
            return MCPMessage(
                trace_id=message.trace_id,
                sender=self.name,
                receiver=message.sender,
                type=MessageType.INGESTION_RESPONSE,
                payload={
                    **response.dict(),
                    'processed_documents': processed_documents
                }
            )
            
        except Exception as e:
            logger.error(f"Error in ingestion: {str(e)}")
            error_response = IngestionResponse(
                success=False,
                processed_files=[],
                chunks_created=0,
                error_message=str(e)
            )
            
            return MCPMessage(
                trace_id=message.trace_id,
                sender=self.name,
                receiver=message.sender,
                type=MessageType.INGESTION_RESPONSE,
                payload=error_response.dict()
            )