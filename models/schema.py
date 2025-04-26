from typing import Dict, Any, TypedDict, List, Optional
from pydantic import BaseModel

class WorkflowState(TypedDict):
    query: str
    retrieved_docs: list[str] | None
    source_names: list[str] | None
    reasoning_output: str | None
    response: str | None
    metadata: Dict[str, Any] | None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None