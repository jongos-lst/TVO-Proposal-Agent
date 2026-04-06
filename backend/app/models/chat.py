from pydantic import BaseModel, Field
from typing import Optional
import uuid


class ChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str


class ChatResponse(BaseModel):
    session_id: str
    phase: str
    message: str
    structured_data: Optional[dict] = None
