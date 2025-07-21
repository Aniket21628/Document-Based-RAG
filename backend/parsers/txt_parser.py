import markdown
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class TXTParser:
    @staticmethod
    def parse(file_path: str) -> Dict[str, any]:
        """Parse TXT/Markdown files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Check if it's markdown
            file_type = "txt"
            if file_path.lower().endswith(('.md', '.markdown')):
                file_type = "markdown"
                # Convert markdown to plain text for better processing
                html = markdown.markdown(content)
                # Simple HTML tag removal
                import re
                content = re.sub('<[^<]+?>', '', html)
            
            metadata = {
                "file_type": file_type,
                "file_path": file_path,
                "character_count": len(content),
                "word_count": len(content.split())
            }
            
            return {
                "content": content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing TXT/MD {file_path}: {str(e)}")
            raise Exception(f"Failed to parse TXT/MD: {str(e)}")