import pandas as pd
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class CSVParser:
    @staticmethod
    def parse(file_path: str) -> Dict[str, any]:
        """Parse CSV and convert to text content"""
        try:
            df = pd.read_csv(file_path)
            
            # Convert DataFrame to readable text
            text_content = f"CSV Data Summary:\n"
            text_content += f"Columns: {', '.join(df.columns.tolist())}\n"
            text_content += f"Number of rows: {len(df)}\n\n"
            
            # Add column descriptions
            text_content += "Column Information:\n"
            for col in df.columns:
                text_content += f"- {col}: {df[col].dtype}\n"
            
            text_content += "\nData Preview:\n"
            text_content += df.head(10).to_string(index=False)
            
            # Add statistical summary for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                text_content += "\n\nNumerical Statistics:\n"
                text_content += df[numeric_cols].describe().to_string()
            
            metadata = {
                "num_rows": len(df),
                "num_columns": len(df.columns),
                "columns": df.columns.tolist(),
                "file_type": "csv",
                "file_path": file_path
            }
            
            return {
                "content": text_content,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing CSV {file_path}: {str(e)}")
            raise Exception(f"Failed to parse CSV: {str(e)}")