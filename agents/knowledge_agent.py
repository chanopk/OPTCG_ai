
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Fix for "sqlite3.OperationalError: no such table: collections" in new threads
# ChromaDB might have issues with concurrency or multiple instances if not handled 
# but for now we basically re-instantiate service inside the tool or globally.
# Given it's a tool, re-instantiating might be safer or passing a singleton.
# We will duplicate the import here to be safe with path.
from app.services.search import HybridSearchService

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

@tool
def search_rule_knowledge(query: str):
    """
    Search for Official Rules of One Piece Card Game.
    Useful for answering questions about game flow, combat steps, keywords, and specific interactions.
    """
    service = HybridSearchService()
    return service.retrieve_rules(query)

tools = [search_card_knowledge, search_rule_knowledge]

# Define State
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Define Agent Node
def agent(state: AgentState):
    # Use Gemini-1.5-pro or flash. Let's try gemini-1.5-flash for speed if desired, or pro for quality. //
    # Defaulting to 1.5-pro as in spec.
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

def should_continue(state: AgentState) -> Literal["tools", END]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

builder.add_conditional_edges("agent", should_continue)
builder.add_edge("tools", "agent")

graph = builder.compile()

def run_agent(query: str):
    """
    Helper function to run the agent with a single query.
    """
    print(f"User: {query}")
    inputs = {"messages": [HumanMessage(content=query)]}
    for chunk in graph.stream(inputs, stream_mode="values"):
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
        run_agent("What does Monkey D. Luffy Leader card do?")
