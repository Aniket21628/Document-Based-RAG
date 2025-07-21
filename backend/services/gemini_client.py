import google.generativeai as genai
from typing import List, Dict, Any
import logging
from config import Config

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate_response(self, query: str, context_chunks: List[str]) -> str:
        """Generate response using Gemini with retrieved context"""
        try:
            # Prepare context
            context = "\n\n".join(context_chunks)
            
            # Create prompt
            prompt = f"""Based on the following context from uploaded documents, please answer the user's question.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, accurate answer based on the context
- If the answer isn't in the context, say so
- Include relevant details from the context
- Be concise but comprehensive

Answer:"""

            # Generate response
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response with Gemini: {e}")
            raise
    
    async def summarize_document(self, content: str) -> str:
        """Summarize document content"""
        try:
            prompt = f"Please provide a concise summary of the following document content:\n\n{content[:4000]}..."
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            raise