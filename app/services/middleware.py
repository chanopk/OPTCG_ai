from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END

from app.services.guardrails import LocalGuardrailsProvider, AzureGuardrailsProvider

# Initialize Providers
local_provider = LocalGuardrailsProvider()
azure_provider = AzureGuardrailsProvider()

# Define Middleware Nodes for LangGraph

# --- Local Guards ---
async def local_input_guard(state: Dict[str, Any]):
    """
    Local Middleware Node: Validates input using Local Guardrails.
    """
    messages = state["messages"]
    if not messages:
        return {"messages": messages}
    
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        validation = await local_provider.validate_input(last_message.content)
        if not validation["valid"]:
            raise ValueError(f"Local Guardrails Input Error: {validation['error']}")
        
        if validation["refined_query"] != last_message.content:
            return {"messages": [HumanMessage(content=validation["refined_query"])]}
            
    return {}

async def local_output_guard(state: Dict[str, Any]):
    """
    Local Middleware Node: Validates output using Local Guardrails.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, AIMessage) or (hasattr(last_message, "type") and last_message.type == "ai"):
        validation = await local_provider.validate_output(last_message.content)
        if not validation["valid"]:
             raise ValueError(f"Local Guardrails Output Error: {validation['error']}")
             
    return {}

# --- Azure Guards ---
async def azure_input_guard(state: Dict[str, Any]):
    """
    Azure Middleware Node: Validates input using Azure AI Content Safety.
    """
    messages = state["messages"]
    if not messages:
        return {"messages": messages}
    
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        validation = await azure_provider.validate_input(last_message.content)
        if not validation["valid"]:
            raise ValueError(f"Azure Guardrails Input Error: {validation['error']}")
        
        if validation["refined_query"] != last_message.content:
            return {"messages": [HumanMessage(content=validation["refined_query"])]}

    return {}

async def azure_output_guard(state: Dict[str, Any]):
    """
    Azure Middleware Node: Validates output using Azure AI Content Safety.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, AIMessage) or (hasattr(last_message, "type") and last_message.type == "ai"):
        validation = await azure_provider.validate_output(last_message.content)
        if not validation["valid"]:
             raise ValueError(f"Azure Guardrails Output Error: {validation['error']}")

    return {}
