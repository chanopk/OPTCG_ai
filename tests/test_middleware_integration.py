import pytest
import sys
import os
from langchain_core.messages import HumanMessage

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.knowledge_agent import graph

@pytest.mark.asyncio
async def test_middleware_off_topic():
    # "วิธีทำส้มตำ" triggers our mock topic guard
    # Should raise ValueError which API converts to 400
    # Here we expect the graph (or middleware) to raise the error directly
    with pytest.raises(ValueError, match="Guardrails Input Error"):
        await graph.ainvoke({"messages": [HumanMessage(content="ขอวิธีทำส้มตำ")]})

@pytest.mark.asyncio
async def test_middleware_pii_redaction():
    # This shouldn't raise error, but pass redacted query to agent.
    # Since agent execution involves LLM call, this test might be flaky or require mocking LLM.
    # For now, we assume the agent runs and we just want to ensure NO ERROR is raised 
    # and preferably the output reflects safety (though we can't easily assert redaction inside without tracing).
    # We will just assert it runs successfully.
    
    # Note: Running this might hit real LLM API. 
    # Use a mock query that is valid but simple.
    
    try:
        result = await graph.ainvoke({"messages": [HumanMessage(content="My phone is 081-123-4567")]})
        assert result is not None
        last_message = result["messages"][-1].content
        # Check if agent output is present
        assert isinstance(last_message, str)
        # We can't strictly assert logic here without mocking, but we assert stability.
    except Exception as e:
        pytest.fail(f"Graph execution failed: {e}")
