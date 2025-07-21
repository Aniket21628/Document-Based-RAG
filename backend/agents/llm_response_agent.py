import google.generativeai as genai
from agents.base_agent import BaseAgent
from mcp.message_types import MCPMessage, MessageType, LLMRequest, LLMResponse
from config import config
from typing import Optional, List, Dict
import logging
import re

logger = logging.getLogger(__name__)

class LLMResponseAgent(BaseAgent):
    def __init__(self):
        super().__init__("LLMResponseAgent")
        
        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        self.subscribe_to_messages([MessageType.LLM_REQUEST])
    
    async def process_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Process LLM request"""
        if message.type == MessageType.LLM_REQUEST:
            return await self.handle_llm_request(message)
        return None
    
    def create_prompt(self, query: str, context: str, conversation_history: List[Dict[str, str]]) -> str:
        """Create a well-structured prompt for Gemini"""
        
        # Build conversation history
        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious Conversation:\n"
            for turn in conversation_history[-3:]:  # Last 3 turns
                history_text += f"User: {turn.get('user', '')}\n"
                history_text += f"Assistant: {turn.get('assistant', '')}\n"
        
        prompt = f"""You are a helpful AI assistant that answers questions based on provided document context. 

CONTEXT FROM DOCUMENTS:
{context}

{history_text}

CURRENT QUESTION: {query}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, clearly state what information is missing. Always cite which parts of the context you're using to support your answer.

Rules:
1. Base your answer primarily on the provided context
2. Be specific and detailed in your response
3. If you mention specific data or facts, indicate which document/source it came from
4. If the context is insufficient, clearly state what additional information would be needed
5. Maintain a helpful and professional tone

Answer:"""
        
        return prompt
    
    def extract_sources(self, context: str, retrieved_chunks: List[Dict]) -> List[str]:
        """Extract source information from retrieved chunks"""
        sources = []
        for chunk in retrieved_chunks:
            metadata = chunk.get('metadata', {})
            file_path = metadata.get('file_path', 'Unknown')
            file_type = metadata.get('file_type', 'Unknown')
            
            # Create a readable source reference
            filename = file_path.split('/')[-1] if '/' in file_path else file_path
            source = f"{filename} ({file_type})"
            
            if 'chunk_index' in metadata:
                source += f" - Section {metadata['chunk_index'] + 1}"
            
            if source not in sources:
                sources.append(source)
        
        return sources
    
    async def handle_llm_request(self, message: MCPMessage) -> MCPMessage:
        """Handle LLM generation request"""
        try:
            request_data = LLMRequest(**message.payload)
            
            # Create prompt
            prompt = self.create_prompt(
                query=request_data.query,
                context=request_data.context,
                conversation_history=request_data.conversation_history
            )
            
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            answer = response.text
            
            # Extract sources from retrieved chunks if available
            sources = []
            if 'retrieved_chunks' in message.payload:
                sources = self.extract_sources(
                    request_data.context, 
                    message.payload['retrieved_chunks']
                )
            
            # Calculate confidence (simple heuristic)
            confidence = min(0.9, len(request_data.context) / 2000)  # Higher confidence with more context
            
            llm_response = LLMResponse(
                answer=answer,
                sources=sources,
                confidence=confidence
            )
            
            return MCPMessage(
                trace_id=message.trace_id,
                sender=self.name,
                receiver=message.sender,
                type=MessageType.LLM_RESPONSE,
                payload=llm_response.dict()
            )
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return MCPMessage(
                trace_id=message.trace_id,
                sender=self.name,
                receiver=message.sender,
                type=MessageType.ERROR,
                payload={'error': f"LLM generation failed: {str(e)}"}
            )