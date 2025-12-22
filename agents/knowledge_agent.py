
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from app.services.rule_loader import load_comprehensive_rules

# Load Environment Variables
load_dotenv()

# Fix for "sqlite3.OperationalError: no such table: collections" in new threads
# ChromaDB might have issues with concurrency or multiple instances if not handled 
# but for now we basically re-instantiate service inside the tool or globally.
# Given it's a tool, re-instantiating might be safer or passing a singleton.
# We will duplicate the import here to be safe with path.
from app.services.search import HybridSearchService
from app.services.middleware import (
    local_input_guard, azure_input_guard, 
    local_output_guard, azure_output_guard
)

# Initialize Service once if possible, or inside tool to avoid Pickling issues
# But Chroma client might need to be created in the main thread or consistently.
# Let's instantiate inside to be safe for now, or use a global lazy loader.

@tool
def search_card_knowledge(query: str, k: int = 10):
    """
    Search for One Piece Card Game information using Hybrid Search.
    Useful for retrieving card effects, stats, attributes, and rule interactions.
    You can increase 'k' (e.g., to 20 or 50) if the initial results are missing the card you are looking for or if you need a broader search.
    """
    # Instantiate service on demand to ensure thread safety with SQLite/Chroma if needed
    service = HybridSearchService()
    return service.retrieve_card_data(query, k=k)

tools = [search_card_knowledge]

# Define State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Load Rules
RULES_TEXT = load_comprehensive_rules()

# Define Agent Node
SYSTEM_PROMPT = f"""
You are a helpful assistant for the One Piece Card Game.
1. You must always answer in Thai.
2. You are allowed to use English for specific Card Names, Keywords, Abilities, and Technical Terms to maintain accuracy.
3. Do not answer questions unrelated to One Piece Card Game. If asked about other topics, politely refuse in Thai.

Below are the Comprehensive Rules of the game. Use these rules to answer any questions regarding gameplay, steps, effects, or interactions.
If the user asks about a rule, answer confidently based on the text below.

=== COMPREHENSIVE RULES ===
{RULES_TEXT}
===========================
"""

def agent(state: AgentState):
    # change model when limit token is too high
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    # Prepend System Prompt
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    
    return {"messages": [llm_with_tools.invoke(messages)]}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

# Guardrail Nodes
builder.add_node("local_input_guard", local_input_guard)
builder.add_node("azure_input_guard", azure_input_guard)
builder.add_node("local_output_guard", local_output_guard)
builder.add_node("azure_output_guard", azure_output_guard)

# Router Logic for Guardrails
def select_input_guard(state: AgentState) -> Literal["local_input_guard", "azure_input_guard"]:
    provider = os.getenv("GUARDRAILS_PROVIDER", "LOCAL").upper()
    if provider == "AZURE":
        return "azure_input_guard"
    return "local_input_guard"

def select_output_guard_or_tools(state: AgentState):
    # Check if we should go to tools first
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    
    # Otherwise go to Output Guard
    provider = os.getenv("GUARDRAILS_PROVIDER", "LOCAL").upper()
    if provider == "AZURE":
        return "azure_output_guard"
    return "local_output_guard"

# Edges
# START -> Input Guard
builder.add_conditional_edges(START, select_input_guard)

# Input Guard -> Agent (Both paths lead to agent)
builder.add_edge("local_input_guard", "agent")
builder.add_edge("azure_input_guard", "agent")

# Agent -> Tools OR Output Guard
builder.add_conditional_edges("agent", select_output_guard_or_tools)

# Tools -> Agent
builder.add_edge("tools", "agent")

# Output Guard -> END
builder.add_edge("local_output_guard", END)
builder.add_edge("azure_output_guard", END)

graph = builder.compile()

import asyncio

async def run_agent(query: str):
    """
    Helper function to run the agent with a single query.
    """
    print(f"User: {query}")
    inputs = {"messages": [HumanMessage(content=query)]}
    async for chunk in graph.astream(inputs, stream_mode="values"):
        message = chunk["messages"][-1]
        if message.content:
            print(f"Agent: {message.content}")
        # if hasattr(message, 'tool_calls') and message.tool_calls:
        #     print(f"Tool Call: {message.tool_calls}")

if __name__ == "__main__":
    # Test run
    # Ensure GOOGLE_API_KEY is set in environment
    if "GOOGLE_API_KEY" not in os.environ:
        print("Please set GOOGLE_API_KEY environment variable.")
    else:
        asyncio.run(run_agent("What does Monkey D. Luffy Leader card do?"))
