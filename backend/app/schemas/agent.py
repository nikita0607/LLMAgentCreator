from typing import Optional, Dict, Any, List
from pydantic import BaseModel


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

class NodeParam(BaseModel):
    name: str
    description: str
    value: Optional[str] = None

class ConditionalBranch(BaseModel):
    id: str
    condition_text: str  # Текстовое описание условия
    next_node: Optional[str] = None

class NodeLogic(BaseModel):
    id: str
    text: str
    type: str  # "webhook", "knowledge", "conditional_llm", "forced_message", "wait_for_user_input"
    next: Optional[str] = None
    action: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    params: Optional[List[NodeParam]] = []
    missing_param_message: Optional[str] = None
    on_success: Optional[str] = None
    on_failure: Optional[str] = None
    # Новые поля для conditional_llm
    branches: Optional[List[ConditionalBranch]] = []
    default_branch: Optional[str] = None  # Узел по умолчанию, если ни одно условие не подошло
    # Поле для forced_message
    forced_text: Optional[str] = None  # Принудительное сообщение для автоматической отправки
    position: Dict[str, Any] = None  # {"x": float, "y": float}

class AgentLogic(BaseModel):
    nodes: List[NodeLogic]
    start_node: Optional[str] = None

class AgentUpdate(BaseModel):
    logic: AgentLogic