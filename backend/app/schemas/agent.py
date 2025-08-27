from pydantic import BaseModel
from typing import Optional, Dict, Any

class AgentBase(BaseModel):
    name: str
    system_prompt: str
    voice_id: str
    logic: Optional[Dict[str, Any]] = None

class AgentCreate(AgentBase):
    pass

class AgentOut(AgentBase):
    id: int
    class Config:
        from_attributes = True


from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class NodeParam(BaseModel):
    name: str
    description: str
    value: Optional[str] = None

class NodeLogic(BaseModel):
    id: str
    text: str
    type: str  # "message" или "webhook"
    next: Optional[str] = None
    action: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    params: Optional[List[NodeParam]] = []
    missing_param_message: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    position: Dict[str, Any] = None  # {"x": float, "y": float}

class AgentLogic(BaseModel):
    nodes: List[NodeLogic]
    start_node: Optional[str] = None

class AgentUpdate(BaseModel):
    logic: AgentLogic