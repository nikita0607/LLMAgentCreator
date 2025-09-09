from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentOut
from app.core.security import get_current_user
from app.schemas.agent import AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/", response_model=AgentOut)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_agent = Agent(**agent.dict(), owner_id=current_user.id)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.get("/", response_model=List[AgentOut])
def list_agents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Agent).filter(Agent.owner_id == current_user.id).all()

@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(agent_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_agent = db.query(Agent).filter(Agent.id == agent_id, Agent.owner_id == current_user.id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return db_agent

@router.put("/{agent_id}", response_model=AgentUpdate)
def update_agent(agent_id: int, agent_update: AgentUpdate, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Дебаг: проверяем forced_message ноды
    logic_dict = agent_update.logic.dict()
    for node in logic_dict.get("nodes", []):
        if node.get("type") == "forced_message":
            print(f"Saving forced_message node {node.get('id')} with forced_text: {node.get('forced_text')}")
    
    # Сохраняем логику в JSON поле
    agent.logic = logic_dict
    db.commit()
    db.refresh(agent)
    return agent_update

@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    return {"message": "Agent deleted successfully"}