import pytest
import os
import sys
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.guardrails.azure_provider import AzureGuardrailsProvider

# Load environment variables
load_dotenv()

# Skip if credentials are missing
def has_azure_credentials():
    return bool(os.getenv("AZURE_CONTENT_SAFETY_ENDPOINT") and os.getenv("AZURE_CONTENT_SAFETY_KEY"))

@pytest.mark.skipif(not has_azure_credentials(), reason="Azure credentials not found")
@pytest.mark.asyncio
async def test_azure_safe_query():
    """
    Test that a safe query passes Azure Guardrails.
    """
    provider = AzureGuardrailsProvider()
    safe_query = "Hello, how do I play One Piece Card Game?"
    
    result = await provider.validate_input(safe_query)
    
    assert result["valid"] is True, f"Safe query failed: {result.get('error')}"
    assert result["error"] is None

@pytest.mark.skipif(not has_azure_credentials(), reason="Azure credentials not found")
@pytest.mark.asyncio
async def test_azure_unsafe_query():
    """
    Test that an unsafe query is blocked by Azure Guardrails.
    """
    provider = AzureGuardrailsProvider()
    # Unsafe content (Hate/Violence)
    unsafe_query = "I hate you, you should die and kill everyone."
    
    result = await provider.validate_input(unsafe_query)
    
    # Expect blockage
    assert result["valid"] is False, "Unsafe query should have been blocked"
    assert "Azure Content Safety Alert" in result["error"]
