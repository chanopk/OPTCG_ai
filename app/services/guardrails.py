import re
import json
from typing import Optional, List, Dict, Any
from guardrails import Guard
# from guardrails.hub import RegexMatch
# Note: In a real scenario, we might import specific validators from guardrails.hub
# For this educational implementation, we will build some custom logic or use simple available ones.
# Since we might not want to depend on external Hub downloads which might require API keys or network,
# we will implement lightweight custom validators or use LLM-based validation.

from pydantic import BaseModel, Field

class GuardrailsManager:
    """
    Manager for handling various types of Guardrails for the OPTCG AI Service.
    Demonstrates:
    1. Input Guards (Topic, Security)
    2. Output Guards (Structure, Quality)
    """

    def __init__(self):
        # We can initialize specific guards here
        pass

    async def validate_input(self, query: str) -> Dict[str, Any]:
        """
        Run all input guardrails.
        Returns a dict with 'valid': bool, 'refined_query': str, 'error': str
        """
        # 1. PII Guard (Redaction)
        # Simple regex for phone numbers (educational demo)
        # Matches 08x-xxx-xxxx or similar
        pii_refined_query = re.sub(r'0\d{1,2}-\d{3}-\d{4}', '<PHONE_REDACTED>', query)
        
        # 2. Injection Guard (Basic Keyword Block)
        forbidden_keywords = ["ignore all instructions", "format c:", "rm -rf"]
        for keyword in forbidden_keywords:
            if keyword.lower() in pii_refined_query.lower():
                return {"valid": False, "error": "Security Alert: Possible Prompt Injection detected.", "refined_query": query}

        # 3. Topic Guard (Relevance)
        # For simplicity/speed, we might do a heuristic check or use a small LLM call.
        # Here we verify if it's broadly about One Piece, Card Games, or conversational greetings.
        # A robust implementation would use an LLM classifier. 
        # For this demo, let's allow it unless it's obviously off-topic (mock logic or simple keyword for now).
        # We will assume valid for now to avoid blocking valid general questions, 
        # but in a real 'Topic Guard', checking via LLM is best.
        
        # 3. Topic Guard (Relevance) - Mock Implementation
        # For this demo, we explicitly block known off-topic keywords to demonstrate the flow.
        off_topic_keywords = ["food", "cooking", "shabu", "sontam", "resipe", "วิธีทำ"]
        for keyword in off_topic_keywords:
            if keyword in query.lower():
                 return {"valid": False, "error": "Topic Alert: This AI is focused on One Piece Card Game only.", "refined_query": query}
        
        return {"valid": True, "refined_query": pii_refined_query, "error": None}

    async def validate_output(self, response: str) -> Dict[str, Any]:
        """
        Run output guardrails.
        """
        # 1. Toxicity Check (Mock/Basic)
        bad_words = ["damn", "stupid", "idiot"] # Educational example
        for word in bad_words:
            if word in response.lower():
                 return {"valid": False, "error": "Quality Alert: Toxic content detected.", "refined_response": None}

        # 2. Structure Check (Optional - if we expected JSON)
        # If response starts with '{', try to parse it.
        if response.strip().startswith("{"):
            try:
                json.loads(response)
            except json.JSONDecodeError:
                 return {"valid": False, "error": "Structure Alert: Invalid JSON format.", "refined_response": response}

        return {"valid": True, "refined_response": response, "error": None}

# Singleton instance
guardrails_service = GuardrailsManager()
