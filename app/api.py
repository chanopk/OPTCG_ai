from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from langfuse.langchain import CallbackHandler
import time

from app.schemas import ChatRequest, ChatResponse, ChatMetadata
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
    try:
        inputs = {"messages": [HumanMessage(content=request.query)]}
        
        # Initialize Langfuse CallbackHandler
        # It automatically picks up credentials from os.environ
        langfuse_handler = CallbackHandler()
        
        start_time = time.time()
        
        # Run the graph with callbacks
        # Using stream or invoke. Invoke is simpler for single response.
        result = await graph.ainvoke(
            inputs,
            config={"callbacks": [langfuse_handler]}
        )
        
        execution_time = time.time() - start_time
        
        # Extract the last message content
        messages = result["messages"]
        last_message = messages[-1]
        
        # Construct Metadata
        # langfuse_handler.flush() # Not always needed if background thread is used
        
        trace_id = None
        # Try to safely get trace id if available
        if hasattr(langfuse_handler, "trace") and langfuse_handler.trace:
            trace_id = langfuse_handler.trace.id
        elif hasattr(langfuse_handler, "get_trace_id"):
             # Some versions might have this
             try:
                trace_id = langfuse_handler.get_trace_id()
             except:
                pass
        
        metadata = ChatMetadata(
            trace_id=trace_id,
            execution_time=execution_time,
        )
        
        return ChatResponse(
            response=last_message.content,
            metadata=metadata
        )
    except ValueError as ve:
        # Catch Guardrails errors (raised as ValueError in middleware)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # In production, we should log the error
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
