import PyPDF2 # type: ignore
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PDFParser:
    @staticmethod
    def parse(file_path: str) -> Dict[str, any]:
        """Parse PDF and extract text content"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                text_content = ""
                metadata = {
                    "num_pages": len(pdf_reader.pages),
                    "file_type": "pdf",
                    "file_path": file_path
                }
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}"
                
                return {
                    "content": text_content,
                    "metadata": metadata
                }
                
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise Exception(f"Failed to parse PDF: {str(e)}")