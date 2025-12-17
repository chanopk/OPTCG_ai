import os
from dotenv import load_dotenv

# Load env before importing other things that might need it
load_dotenv()

from agents.knowledge_agent import run_agent

if __name__ == "__main__":
    print("--- Testing LangGraph Knowledge Agent ---")
    query = "Tell me about the effect of Shanks (OP01-120)."
    try:
        run_agent(query)
    except Exception as e:
        print(f"Error running agent: {e}")
