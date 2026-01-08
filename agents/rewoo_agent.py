import os
import sys
import asyncio
from typing import Annotated, TypedDict, List, Literal

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
# from langgraph.prebuilt import ToolExecutor # Not using prebuilt for custom execution logic

from app.services.search import HybridSearchService

# Load Env
load_dotenv()

# --- 1. State Definition ---
class PlanExecuteState(TypedDict):
    input: str
    plan: List[tuple[str, str]] # List of (tool_name, query)
    results: List[str]          # Execution results
    response: str               # Final answer
    token_usage: dict           # Token usage stats: {"total_tokens": 0, "planner_tokens": 0, "solver_tokens": 0}

# --- 2. Tool Definitions (Simulated for Executor) ---
# We reuse the logic from knowledge_agent but call service directly in Executor
service = HybridSearchService()

def run_search_card(query: str):
    return service.retrieve_card_data(query)

def run_search_rules(query: str):
    return service.retrieve_rules(query)

# --- 3. Planner Node ---
# Output Structure for Planner
class Step(BaseModel):
    tool: Literal["search_card", "search_rules"] = Field(description="The tool to use: 'search_card' for card info, 'search_rules' for game rules.")
    query: str = Field(description="The search query for the tool.")

class Plan(BaseModel):
    steps: List[Step] = Field(description="List of steps to execute.")

def planner(state: PlanExecuteState):
    print("--- Planner ---")
    question = state["input"]
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
    
    # Force structured output
    # include_raw=True to capture token usage
    planner_llm = llm.with_structured_output(Plan, include_raw=True)
    
    system_prompt = """
    You are a Planner for the One Piece Card Game Assistant.
    Your job is to break down the user's question into a list of specific search steps.
    
    Available Tools:
    1. search_card: Use this to find Card Effects, Power, Type, Color, Traits availability.
    2. search_rules: Use this to find Game Rules, Phase info, Keyword definitions (e.g., "Double Attack", "Blocker").
    
    Rules:
    - **Ambiguity Handling**: If the user provides a name that could be a Leader or a Character (e.g., "Luffy", "Yamato") and DOES NOT specify the type:
      - Generate a BROAD query to catch all variations (e.g., "Monkey D. Luffy").
      - DO NOT guess or limit to just "Leader" or "Character" unless explicitly asked.
    - If the user asks about a card's interaction with a rule, create TWO steps: one for the card, one for the rule.
    - If the user asks to compare two cards, create TWO steps: one for each card.
    - Generate specific, concise queries.
    """
    
    output = planner_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ])
    
    plan: Plan = output["parsed"]
    raw_response = output["raw"]
    
    # Extract token usage
    usage = {"total_tokens": 0, "planner_tokens": 0, "solver_tokens": 0}
    if hasattr(raw_response, "usage_metadata") and raw_response.usage_metadata:
        usage["planner_tokens"] = raw_response.usage_metadata.get("total_tokens", 0)
        usage["total_tokens"] += usage["planner_tokens"]
        print(f"Planner Token Usage: {usage['planner_tokens']}")
    
    
    # Convert Pydantic to simple list of tuples for state
    plan_data = [(step.tool, step.query) for step in plan.steps]
    print(f"Plan Generated: {plan_data}")
    
    return {"plan": plan_data, "token_usage": usage}

# --- 4. Executor Node ---
def executor(state: PlanExecuteState):
    print("--- Executor ---")
    plan = state["plan"]
    results = []
    
    for tool_name, query in plan:
        print(f"Executing: {tool_name}('{query}')")
        if tool_name == "search_card":
            res = run_search_card(query)
            results.append(f"[Result from search_card('{query}')]:\n{res}")
        elif tool_name == "search_rules":
            res = run_search_rules(query)
            results.append(f"[Result from search_rules('{query}')]:\n{res}")
        else:
            results.append(f"Error: Unknown tool {tool_name}")
            
    return {"results": results}

# --- 5. Solver Node ---
def solver(state: PlanExecuteState):
    print("--- Solver ---")
    question = state["input"]
    results = state["results"]
    usage = state.get("token_usage", {"total_tokens": 0, "planner_tokens": 0, "solver_tokens": 0})
    
    # Join results into a context block
    context = "\n\n".join(results)
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
    
    system_prompt = """
    You are a helpful assistant for the One Piece Card Game.
    Answer the user's question based ONLY on the provided Context below.
    
    1. **Language**: You must always answer in Thai.
    2. **Terminology**: Use English for specific technical terms or card names if appropriate (e.g. "Double Attack", "Blocker").
    3. **Ambiguity Resolution**: 
       - If the search results contain *multiple* cards with the same name (e.g., a "Leader" version and a "Character" version of Luffy):
       - **You MUST explicitly separate the details for each type.**
       - Use bullet points or sections to explain: "สำหรับ Leader Luffy Effect คือ..." AND "สำหรับ Character Luffy Effect คือ..."
       - Do not mix them up.
    4. **Synthesis**: Synthesize the information from multiple results to form a coherent answer.
    """
    
    user_message = f"""
    Question: {question}
    
    Context from Search:
    {context}
    """
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ])
    
    # Extract Token Usage
    solver_tokens = 0
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        solver_tokens = response.usage_metadata.get("total_tokens", 0)
        print(f"Solver Token Usage: {solver_tokens}")
    
    usage["solver_tokens"] = solver_tokens
    usage["total_tokens"] += solver_tokens
    
    return {"response": response.content, "token_usage": usage}

# --- 6. Graph Construction ---
workflow = StateGraph(PlanExecuteState)

workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("solver", solver)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "solver")
workflow.add_edge("solver", END)

graph = workflow.compile()

# --- Test Main ---
async def main():
    # Test Question that might be ambiguous
    question = "ST21 diff ST01 leader luffy ?" #"luffy effect คืออะไร" # Ambiguous: Could be Leader or Character
    print(f"User: {question}")
    
    inputs = {"input": question}
    
    final_usage = None
    
    async for chunk in graph.astream(inputs):
        for node, values in chunk.items():
            if "token_usage" in values:
                final_usage = values["token_usage"]
            
            if node == "solver":
                print(f"\nFinal Answer:\n{values['response']}")
    
    if final_usage:
        print(f"\nTotal Token Usage: {final_usage['total_tokens']} (Planner: {final_usage['planner_tokens']}, Solver: {final_usage['solver_tokens']})")

if __name__ == "__main__":
    asyncio.run(main())
