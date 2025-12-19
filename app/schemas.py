from pydantic import BaseModel

from typing import Optional, List, Any

class ChatRequest(BaseModel):
    query: str

class ChatMetadata(BaseModel):
    trace_id: Optional[str] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    execution_time: Optional[float] = None
    steps: Optional[List[Any]] = None

class ChatResponse(BaseModel):
    response: str
    metadata: Optional[ChatMetadata] = None
