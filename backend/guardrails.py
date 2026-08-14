import re
import logging
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class SecurityGuard:
    def __init__(self):
        # 1. Prompt Injection Patterns
        self.injection_patterns = [
            r"ignore previous instructions",
            r"ignore all previous instructions",
            r"system prompt",
            r"you are now",
            r"bypass",
            r"jailbreak",
            r"forget everything",
            r"do not follow",
            r"new instructions",
            r"disregard",
            r"print previous",
            r"\bdan\b", # Do Anything Now
        ]
        
        # 2. SQL / Command Injection Patterns
        self.code_injection_patterns = [
            r"DROP TABLE",
            r"UNION SELECT",
            r"OR 1=1",
            r"exec\(",
            r"eval\(",
            r"__import__",
            r"os\.system",
            r";\s*rm -rf",
            r"chmod 777"
        ]
        
        # 3. Toxicity / Profanity Patterns
        self.toxicity_patterns = [
            r"\b(fuck|shit|bitch|asshole|cunt|dick)\b",
        ]
        
        # 4. PII Patterns
        self.pii_patterns = {
            "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "PHONE": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
            "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b"
        }
        
        self.MAX_QUERY_LENGTH = 1000

    def check_input(self, query: str) -> Tuple[bool, str, str]:
        """
        Check the query against all guardrails.
        Returns: (is_safe, processed_query, error_message)
        """
        if not query or not query.strip():
            return False, query, "Query cannot be empty."

        # 1. DoS / Length Check
        if len(query) > self.MAX_QUERY_LENGTH:
            logger.warning("Guardrail triggered: Query length exceeded")
            return False, query, f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH} characters."

        query_lower = query.lower()

        # 2. Prompt Injection Check
        for pattern in self.injection_patterns:
            if re.search(pattern, query_lower):
                logger.warning(f"Guardrail triggered: Prompt injection attempt detected ({pattern})")
                return False, query, "Your query was blocked due to a potential security policy violation."

        # 3. Code / SQL Injection Check
        for pattern in self.code_injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Guardrail triggered: Code/SQL injection attempt detected ({pattern})")
                return False, query, "Your query was blocked because it contains prohibited commands or code snippets."

        # 4. Toxicity Check
        for pattern in self.toxicity_patterns:
            if re.search(pattern, query_lower):
                logger.warning("Guardrail triggered: Toxic language detected")
                return False, query, "Your query was blocked due to inappropriate language."

        # 5. PII Detection and Redaction (Redact and continue)
        processed_query = query
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, processed_query):
                logger.info(f"Guardrail action: Redacting {pii_type} from query")
                processed_query = re.sub(pattern, f"[{pii_type}_REDACTED]", processed_query)

        return True, processed_query, ""
