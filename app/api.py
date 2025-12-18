from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.schemas import ChatRequest, ChatResponse
# Import the graph from the agents module
# Check relative path: app/api.py -> agents/knowledge_agent.py
# We can use absolute imports since project root is in path or installed package
from agents.knowledge_agent import graph
# from app.services.guardrails import guardrails_service

app = FastAPI(title="OPTCG AI Service")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the OPTCG Knowledge Agent.
    """
    """
    try:
        inputs = {"messages": [HumanMessage(content=request.query)]}
        # Run the graph
        # Using stream or invoke. Invoke is simpler for single response.
        result = await graph.ainvoke(inputs)
        
        # Extract the last message content
        messages = result["messages"]
        last_message = messages[-1]
        
        return ChatResponse(response=last_message.content)
    except ValueError as ve:
        # Catch Guardrails errors (raised as ValueError in middleware)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # In production, we should log the error
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
