from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

class SessionCreate(BaseModel):
    agent_id: int

class SessionOut(BaseModel):
    id: int
    agent_id: int
    user_id: int
    status: str
    current_node: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class MessageIn(BaseModel):
    text: str

class MessageOut(BaseModel):
    reply: str
    action: Optional[Dict[str, Any]] = None

class MessageHistory(BaseModel):
    id: int
    sender: str
    text: str
    action: Optional[Dict[str, Any]] = None
    created_at: datetime
    class Config:
        from_attributes = True

class SessionWithHistory(SessionOut):
    messages: List[MessageHistory]