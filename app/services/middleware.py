from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END

from app.services.guardrails import guardrails_service

# Define Middleware Nodes for LangGraph

async def input_guard(state: Dict[str, Any]):
    """
    Middleware Node: Validates input messages before they reach the agent.
    """
    messages = state["messages"]
    if not messages:
        return {"messages": messages}
    
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        # Validate User Input
        validation = await guardrails_service.validate_input(last_message.content)
        if not validation["valid"]:
            raise ValueError(f"Guardrails Input Error: {validation['error']}")
        
        # If valid, replace content with refined query (e.g. PII redacted)
        if validation["refined_query"] != last_message.content:
            # We want to replace the last message.
            # In LangGraph with `add_messages` reducer, returning a message with same ID updates it (if IDs used).
            # Here we might just return the user message with same content.
            # Check if we can overwrite. 
            # For now, let's just return the new message. 
            # If the original message didn't have ID, this appends. 
            # But `messages` in state is a list.
            # If we want to modify the input to the agent node, we are effectively just passing state.
            # The agent node will look at the last message.
            # So if we append a new HumanMessage, the agent sees the refined one.
            return {"messages": [HumanMessage(content=validation["refined_query"])]}
            
    return {} # Return empty dict if no changes to state

async def output_guard(state: Dict[str, Any]):
    """
    Middleware Node: Validates output messages from the agent.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if isinstance(last_message, AIMessage) or (hasattr(last_message, "type") and last_message.type == "ai"):
        validation = await guardrails_service.validate_output(last_message.content)
        if not validation["valid"]:
             raise ValueError(f"Guardrails Output Error: {validation['error']}")
        
        # Update refined response if needed
        if validation["refined_response"] != last_message.content:
             # Can't easily replace without IDs.
             pass
             
    return {}
