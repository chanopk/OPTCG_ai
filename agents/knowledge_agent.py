import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Fix for "sqlite3.OperationalError: no such table: collections" in new threads
from app.services.search import HybridSearchService

@tool
def search_card_knowledge(query: str, k: int = 10):
    """
    Search for One Piece Card Game information using Hybrid Search.
    Useful for retrieving card effects, stats, attributes, and rule interactions.
    You can increase 'k' (e.g., to 20 or 50) if the initial results are missing the card you are looking for or if you need a broader search.
    """
    service = HybridSearchService()
    return service.retrieve_card_data(query, k=k)

@tool
def search_rules_knowledge(query: str):
    """
    Search for official One Piece Card Game Comprehensive Rules.
    Use this when the user asks about game phases, specific keyword definitions, or interaction logic.
    """
    service = HybridSearchService()
    return service.retrieve_rules(query)

tools = [search_card_knowledge, search_rules_knowledge]

# Define State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Define Agent Node
SYSTEM_PROMPT = f"""
You are a helpful assistant for the One Piece Card Game.
1. You must always answer in Thai.
2. You are allowed to use English for specific Card Names, Keywords, Abilities, and Technical Terms to maintain accuracy.
3. If the user asks about Game Rules, Phases, or Keyword Definitions, ALWAYS use the 'search_rules_knowledge' tool.
4. Do not answer questions unrelated to One Piece Card Game. If asked about other topics, politely refuse in Thai.
"""

def agent(state: AgentState):
    # LLM Configuration based on AI_PROVIDER
    provider = os.getenv("AI_PROVIDER", "google_genai").lower()
    
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        
        # OpenRouter uses OpenAI-compatible API
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model=model,
            temperature=0
        )
    elif provider == "ollama":
        # Fallback/Future support for Ollama if needed, currently reusing logic or importing ChatOllama
        from langchain_ollama import ChatOllama
        model = os.getenv("OLLAMA_MODEL", "llama3")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm = ChatOllama(model=model, base_url=base_url, temperature=0)
    else:
        # Default to Google Gemini
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)

    llm_with_tools = llm.bind_tools(tools)
    
    # Prepend System Prompt
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    
    return {"messages": [llm_with_tools.invoke(messages)]}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

# Edges
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()

import asyncio

async def run_agent(query: str):
    """
    Helper function to run the agent with a single query.
    """
    print(f"User: {query}")
    inputs = {"messages": [HumanMessage(content=query)]}
    async for chunk in graph.astream(inputs, stream_mode="values", config={"recursion_limit": 20}):
        message = chunk["messages"][-1]
        if message.content:
            print(f"Agent: {message.content}")
            if hasattr(message, "usage_metadata") and message.usage_metadata:
                print(f"Token Usage: {message.usage_metadata}")
            elif hasattr(message, "response_metadata") and message.response_metadata:
                 # Fallback for some models/versions
                 print(f"Response Metadata: {message.response_metadata.get('usage_metadata') or message.response_metadata.get('token_usage')}")

if __name__ == "__main__":
    # Test run
    # asyncio.run(run_agent("What does ST21 Monkey D. Luffy Leader card do?"))
    asyncio.run(run_agent("ST21 diff ST01 leader luffy ?"))
