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

    # Инициализируем текущий узел из логики агента, если задан
    start_node = None
    try:
        start_node = (agent.logic or {}).get("start_node")
    except Exception:
        start_node = None

    db_session = SessionModel(agent_id=agent.id, user_id=current_user.id, current_node=start_node)
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
    node_id = db_session.current_node or logic.get("start_node")

    if not node_id or node_id not in nodes:
        raise HTTPException(status_code=400, detail="Agent has no valid logic")

    current_node = nodes[node_id]

    # Вызов process_node с использованием conversation_id
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

    # Обновляем текущий узел
    next_node = result.get("next_node")
    if next_node:
        db_session.current_node = next_node

    # Сохраняем conversation_id, чтобы продолжить диалог с LLM
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