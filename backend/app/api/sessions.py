from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.session import Session as SessionModel
from app.models.agent import Agent
from app.schemas.session import SessionCreate, SessionOut, MessageIn, MessageOut
from app.models.user import User
from app.core.security import get_current_user
from app.services.agent_runtime import process_node
from app.models.session_message import SessionMessage
from app.schemas.session import SessionWithHistory


router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionOut)
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = db.query(Agent).filter(Agent.id == session.agent_id, Agent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_session = SessionModel(agent_id=agent.id, user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id, SessionModel.user_id == current_user.id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session


@router.post("/{session_id}/message", response_model=MessageOut)
def send_message(session_id: int, msg: MessageIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Получаем сессию
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Получаем агента
    agent = db.query(Agent).filter(Agent.id == db_session.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Подготовка логики
    logic = agent.logic or {}
    nodes = {n["id"]: n for n in logic.get("nodes", [])}
    
    # Try to get current node, fallback to start node, then to first available node
    node_id = None
    if db_session.current_node and db_session.current_node in nodes:
        node_id = db_session.current_node
    elif logic.get("start_node") and logic.get("start_node") in nodes:
        node_id = logic.get("start_node")
    elif nodes:
        # If all else fails, use the first available node
        node_id = next(iter(nodes))

    if not node_id:
        raise HTTPException(status_code=400, detail=f"No nodes found in agent logic. Logic: {logic}")
    
    if node_id not in nodes:
        raise HTTPException(status_code=400, detail=f"Node '{node_id}' not found in nodes: {list(nodes.keys())}")

    current_node = nodes[node_id]
    
    # Call process_node without cycle detection - allow infinite loops for continuous conversation
    result = process_node(
        nodes,
        current_node,
        agent_id=db_session.agent_id,
        user_input={'user_text': msg.text},
        system_prompt=agent.system_prompt,
        voice_id=agent.voice_id,
        conversation_id=db_session.conversation_id if hasattr(db_session, "conversation_id") else None
    )
    
    # Сохраняем сообщение пользователя
    user_msg = SessionMessage(
        session_id=db_session.id,
        sender="user",
        text=msg.text
    )
    db.add(user_msg)

    # Сохраняем ответ агента
    agent_msg = SessionMessage(
        session_id=db_session.id,
        sender="agent",
        text=result["reply"],
        action=result.get("action")
    )
    db.add(agent_msg)

    # Update current node - allow moving between nodes freely for infinite conversations
    next_node = result.get("next_node")
    if next_node:
        if next_node not in nodes:
            # Don't update to invalid node, stay on current node
            pass
        else:
            db_session.current_node = next_node

    # Save conversation_id to continue LLM dialog
    if "conversation_id" in result:
        db_session.conversation_id = result["conversation_id"]

    db.commit()
    db.refresh(agent_msg)

    return result

@router.get("/{session_id}/history", response_model=SessionWithHistory)
def get_session_history(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return db_session