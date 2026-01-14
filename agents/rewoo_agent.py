import os
import sys
import asyncio
from typing import Annotated, TypedDict, List, Literal

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
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
    plan: List[tuple[str, str, int]] # List of (tool_name, query, k)
    results: List[str]          # Execution results
    response: str               # Final answer
    token_usage: dict           # Token usage stats: {"total_tokens": 0, "planner_tokens": 0, "solver_tokens": 0}
# --- 2. Tool Definitions (Simulated for Executor) ---
# We reuse the logic from knowledge_agent but call service directly in Executor
service = HybridSearchService()

def run_search_card(query: str, k: int = 3):
    return service.retrieve_card_data(query, k=k)

def run_search_rules(query: str, k: int = 3):
    return service.retrieve_rules(query, k=k)

# --- 3. Planner Node ---
# Output Structure for Planner
class Step(BaseModel):
    tool: Literal["search_card", "search_rules", "ask_user"] = Field(description="The tool to use. Use 'ask_user' if clarification is needed.")
    query: str = Field(description="The search query or the question to ask the user.")
    k: int = Field(default=3, description="Number of results to retrieve. Default is 3. Use 1 for specific queries (e.g. ID, Full Name + Set), 3 for moderate specificity.")

class Plan(BaseModel):
    steps: List[Step] = Field(description="List of steps to execute.")

def planner(state: PlanExecuteState):
    print("--- Planner ---")
    question = state["input"]
    
    # Initialize LLM

    # Initialize LLM based on Provider
    provider = os.getenv("AI_PROVIDER", "google_genai").lower()
    if provider == "openrouter":
         llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            temperature=0
        )
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", temperature=0)
    
    # Force structured output
    # include_raw=True to capture token usage
    planner_llm = llm.with_structured_output(Plan, include_raw=True)
    
    system_prompt = """
    You are a Planner for the One Piece Card Game Assistant.
    Your job is to break down the user's question into a list of specific search steps.
    
    Available Tools:
    1. search_card: Use this to find Card Effects, Power, Type, Color, Traits availability.
    2. search_rules: Use this to find Game Rules, Phase info, Keyword definitions.
    3. ask_user: Use this ONLY if the user's query is TOO BROAD or VAGUE (e.g. just "Luffy", "Kaido"). Do not guess. Ask for clarification.
    
    Efficiency Rules (Token Saving):
    - **Very Specific Query** (Contains Card ID e.g., "ST01-001" OR Specific Role e.g. "Leader Luffy ST01"): Set `k=1`.
    - **Specific Query** (Contains Name + Set/Type e.g., "Luffy ST01", "Katukuri Leader"): Set `k=3`.
    - **Broad Query** (Name only, e.g. "Nami"): Use `ask_user` to ask for more details. DO NOT SEARCH.
    
    General Rules:
    - If the user asks about a card's interaction with a rule, create steps for both.
    - If the user asks to compare two cards, create steps for each.
    
    IMPORTANT: You must return the output STRICTLY as a JSON object matching the Plan schema. Do not output markdown code blocks or any other text.
    
    Response Format Example:
    {
      "steps": [
        {
          "tool": "search_card",
          "query": "Luffy Leader ST01",
          "k": 1
        },
        {
          "tool": "ask_user",
          "query": "Which version of Nami do you mean?",
          "k": 3
        }
      ]
    }
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
    # Added 'k' to the tuple structure for Executor
    plan_data = [(step.tool, step.query, step.k) for step in plan.steps]
    print(f"Plan Generated: {plan_data}")
    
    return {"plan": plan_data, "token_usage": usage}

# --- 4. Executor Node ---
def executor(state: PlanExecuteState):
    print("--- Executor ---")
    plan = state["plan"]
    results = []
    
    for item in plan:
        # Unpack based on length to support old format if needed, though we updated planner
        if len(item) == 3:
            tool_name, query, k = item
        else:
            tool_name, query = item
            k = 3 # Default fallback

        print(f"Executing: {tool_name}('{query}', k={k})")
        
        if tool_name == "search_card":
            res = run_search_card(query, k=k)
            results.append(f"[Result from search_card('{query}')]:\n{res}")
        elif tool_name == "search_rules":
            res = run_search_rules(query, k=k)
            results.append(f"[Result from search_rules('{query}')]:\n{res}")
        elif tool_name == "ask_user":
            results.append(f"[CLARIFICATION NEEDED]: {query}")
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
    

    # Initialize LLM based on Provider
    provider = os.getenv("AI_PROVIDER", "google_genai").lower()
    if provider == "openrouter":
         llm = ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            temperature=0
        )
    else:
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
