import os
import json
from typing import Dict, Any
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData, ImageCategory

from dotenv import load_dotenv

load_dotenv()

class AzureGuardrailsProvider:
    """
    Azure AI Content Safety implementation of Guardrails.
    """

    def __init__(self):
        self.endpoint = os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT")
        self.key = os.getenv("AZURE_CONTENT_SAFETY_KEY")
        self.enabled = bool(self.endpoint and self.key)

    async def validate_input(self, query: str) -> Dict[str, Any]:
        """
        Validates input using Azure AI Content Safety (Text).
        """
        if not self.enabled:
             # Fallback or pass-through if not configured (should ideally enforce config check)
             return {"valid": True, "refined_query": query, "error": None}

        try:
            # Create Client (Should ideally be reused or context managed, but for POC this is fine)
            client = ContentSafetyClient(self.endpoint, AzureKeyCredential(self.key))

            # Analyze Text
            request = {"text": query}
            response = client.analyze_text(request)
            
            # Check severities
            # SDK v1.0.0 uses categories_analysis list
            blocks = []
            if response.categories_analysis:
                for result in response.categories_analysis:
                    # Severity is usually int 0-7. Let's block if > 0 (Strict) or > 2 (Medium)
                    # For POC we use strict > 0 to verify it works easily
                    if result.severity > 0:
                        blocks.append(f"{result.category}({result.severity})")

            if blocks:
                return {
                    "valid": False,
                    "error": f"Azure Content Safety Alert: Blocked categories: {', '.join(blocks)}",
                    "refined_query": query
                }

        except HttpResponseError as e:
            # Handle API errors gracefully
            print(f"Azure Content Safety API Error: {e}")
            return {"valid": False, "error": f"Guardrail Service Error: {e}", "refined_query": query}
        except Exception as e:
            return {"valid": False, "error": f"Guardrail Unexpected Error: {e}", "refined_query": query}
        
        return {"valid": True, "refined_query": query, "error": None}

    async def validate_output(self, response: str) -> Dict[str, Any]:
        """
        Validates output using Azure AI Content Safety.
        """
        if not self.enabled:
             return {"valid": True, "refined_response": response, "error": None}

        try:
            client = ContentSafetyClient(self.endpoint, AzureKeyCredential(self.key))
            request = {"text": response}
            analysis = client.analyze_text(request)

            blocks = []
            if analysis.categories_analysis:
                for result in analysis.categories_analysis:
                    if result.severity > 0:
                         blocks.append(f"{result.category}")
            
            if blocks:
                 return {"valid": False, "error": f"Azure Quality Alert: Response contained {', '.join(blocks)} content.", "refined_response": None}
                 
        except Exception as e:
            print(f"Azure Output Guard Error: {e}")
            pass

        return {"valid": True, "refined_response": response, "error": None}
