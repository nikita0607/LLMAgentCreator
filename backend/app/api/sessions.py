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

@router.post("/", response_model=MessageOut)  # Changed response model
def create_session(session: SessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    agent = db.query(Agent).filter(Agent.id == session.agent_id, Agent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_session = SessionModel(agent_id=agent.id, user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # After creating session, check if we need to process initial forced messages
    logic = agent.logic or {}
    nodes = {n["id"]: n for n in logic.get("nodes", [])}
    
    # Find start node
    start_node_id = logic.get("start_node")
    if start_node_id and start_node_id in nodes:
        start_node = nodes[start_node_id]
        
        # If start node is a forced message, process it immediately
        if start_node["type"] == "forced_message":
            messages = []
            conversation_id = None
            max_forced_chain = 10
            forced_chain_count = 0
            current_node_id = start_node_id
            
            # Process forced message chain
            while (current_node_id and current_node_id in nodes and 
                   nodes[current_node_id]["type"] == "forced_message" and 
                   forced_chain_count < max_forced_chain):
                
                forced_chain_count += 1
                current_node = nodes[current_node_id]
                
                result = process_node(
                    nodes,
                    current_node,
                    agent_id=db_session.agent_id,
                    user_input={'user_text': ''},  # Empty input for forced messages
                    system_prompt=agent.system_prompt,
                    voice_id=agent.voice_id,
                    conversation_id=conversation_id
                )
                
                # Save the forced message response
                agent_msg = SessionMessage(
                    session_id=db_session.id,
                    sender="agent",
                    text=result["reply"],
                    action=result.get("action")
                )
                db.add(agent_msg)
                messages.append(agent_msg)
                
                if "conversation_id" in result:
                    conversation_id = result["conversation_id"]
                
                current_node_id = result.get("next_node")
                if not current_node_id or current_node_id not in nodes:
                    break
            
            # Update session state
            db_session.current_node = current_node_id
            if conversation_id:
                db_session.conversation_id = conversation_id
            
            db.commit()
            
            # Return the forced messages as the session creation response
            if messages:
                message_texts = [msg.text for msg in messages]
                return {
                    "reply": message_texts[0] if len(message_texts) == 1 else "",
                    "messages": message_texts,
                    "next_node": current_node_id,
                    "conversation_id": conversation_id,
                    "session_id": db_session.id  # Include session info
                }
    
    # If no forced messages, return basic session creation response
    return {
        "reply": "",  # Empty reply for non-forced message starts
        "next_node": start_node_id,
        "conversation_id": None,
        "session_id": db_session.id
    }

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

    if db_session.agent_id is None:
        raise HTTPException(status_code=404, detail="Agent was deleted")

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
    
    # Сохраняем сообщение пользователя
    user_msg = SessionMessage(
        session_id=db_session.id,
        sender="user",
        text=msg.text
    )
    db.add(user_msg)
    
    # Handle forced message chain first - if current node is forced_message, process it without user input
    conversation_id = db_session.conversation_id if hasattr(db_session, "conversation_id") else None
    messages = []
    max_forced_chain = 10
    forced_chain_count = 0
    current_node_id = node_id
    
    # First, process any forced messages that should run before handling user input
    while (current_node_id and current_node_id in nodes and 
           nodes[current_node_id]["type"] == "forced_message" and 
           forced_chain_count < max_forced_chain):
        
        forced_chain_count += 1
        current_node = nodes[current_node_id]
        
        # Process the forced message node
        result = process_node(
            nodes,
            current_node,
            agent_id=db_session.agent_id,
            user_input={'user_text': ''},  # Empty input for forced messages
            system_prompt=agent.system_prompt,
            voice_id=agent.voice_id,
            conversation_id=conversation_id
        )
        
        # Save the forced message response
        agent_msg = SessionMessage(
            session_id=db_session.id,
            sender="agent",
            text=result["reply"],
            action=result.get("action")
        )
        db.add(agent_msg)
        messages.append(agent_msg)
        
        # Update conversation_id
        if "conversation_id" in result:
            conversation_id = result["conversation_id"]
        
        # Move to next node
        current_node_id = result.get("next_node")
        if not current_node_id or current_node_id not in nodes:
            break
    
    # Now process the user's input with the current node (which should not be a forced_message)
    if current_node_id and current_node_id in nodes:
        current_node = nodes[current_node_id]
        
        # Process user input only if we're not on a forced message node
        if current_node["type"] != "forced_message":
            result = process_node(
                nodes,
                current_node,
                agent_id=db_session.agent_id,
                user_input={'user_text': msg.text},
                system_prompt=agent.system_prompt,
                voice_id=agent.voice_id,
                conversation_id=conversation_id
            )
            
            # Save the response to user's message
            agent_msg = SessionMessage(
                session_id=db_session.id,
                sender="agent",
                text=result["reply"],
                action=result.get("action")
            )
            db.add(agent_msg)
            messages.append(agent_msg)
            
            # Update conversation_id
            if "conversation_id" in result:
                conversation_id = result["conversation_id"]
                
            # Update current node
            current_node_id = result.get("next_node")
            
            # Continue processing any additional forced messages after user response
            while (current_node_id and current_node_id in nodes and 
                   nodes[current_node_id]["type"] == "forced_message" and 
                   forced_chain_count < max_forced_chain):
                
                forced_chain_count += 1
                current_node = nodes[current_node_id]
                
                result = process_node(
                    nodes,
                    current_node,
                    agent_id=db_session.agent_id,
                    user_input={'user_text': ''},
                    system_prompt=agent.system_prompt,
                    voice_id=agent.voice_id,
                    conversation_id=conversation_id
                )
                
                agent_msg = SessionMessage(
                    session_id=db_session.id,
                    sender="agent",
                    text=result["reply"],
                    action=result.get("action")
                )
                db.add(agent_msg)
                messages.append(agent_msg)
                
                if "conversation_id" in result:
                    conversation_id = result["conversation_id"]
                
                current_node_id = result.get("next_node")
                if not current_node_id or current_node_id not in nodes:
                    break
    
    # Update session state
    db_session.current_node = current_node_id
    if conversation_id:
        db_session.conversation_id = conversation_id

    db.commit()
    
    # Return combined response
    if messages:
        # Return individual messages instead of concatenating
        message_texts = [msg.text for msg in messages]
        return {
            "reply": message_texts[0] if len(message_texts) == 1 else "",  # First message as main reply
            "messages": message_texts,  # All messages as separate items
            "next_node": current_node_id,
            "conversation_id": conversation_id
        }
    else:
        # No messages processed (shouldn't happen normally)
        return {
            "reply": "No response generated",
            "next_node": current_node_id,
            "conversation_id": conversation_id
        }

@router.post("/{session_id}/trigger-forced", response_model=MessageOut)
def trigger_forced_messages(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Triggers execution of forced message nodes from the current position.
    Useful for starting automatic message chains without user input.
    """
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
    
    # Try to get current node, fallback to start node
    node_id = None
    if db_session.current_node and db_session.current_node in nodes:
        node_id = db_session.current_node
    elif logic.get("start_node") and logic.get("start_node") in nodes:
        node_id = logic.get("start_node")
    elif nodes:
        node_id = next(iter(nodes))

    if not node_id or node_id not in nodes:
        raise HTTPException(status_code=400, detail="No valid current node found")

    current_node = nodes[node_id]
    
    # Only process if current node is a forced message
    if current_node["type"] != "forced_message":
        raise HTTPException(status_code=400, detail="Current node is not a forced message node")
    
    # Process forced message chain
    messages = []
    conversation_id = db_session.conversation_id if hasattr(db_session, "conversation_id") else None
    max_forced_chain = 10
    forced_chain_count = 0
    current_node_id = node_id
    
    while current_node_id and current_node_id in nodes and forced_chain_count < max_forced_chain:
        current_node = nodes[current_node_id]
        
        if current_node["type"] != "forced_message":
            break
            
        forced_chain_count += 1
        
        # Process the forced message node
        result = process_node(
            nodes,
            current_node,
            agent_id=db_session.agent_id,
            user_input={'user_text': ''},  # Empty input for forced messages
            system_prompt=agent.system_prompt,
            voice_id=agent.voice_id,
            conversation_id=conversation_id
        )
        
        # Save the response
        agent_msg = SessionMessage(
            session_id=db_session.id,
            sender="agent",
            text=result["reply"],
            action=result.get("action")
        )
        db.add(agent_msg)
        messages.append(agent_msg)
        
        # Update conversation_id
        if "conversation_id" in result:
            conversation_id = result["conversation_id"]
        
        # Move to next node
        current_node_id = result.get("next_node")
    
    # Update session state
    db_session.current_node = current_node_id
    if conversation_id:
        db_session.conversation_id = conversation_id

    db.commit()
    
    if not messages:
        raise HTTPException(status_code=400, detail="No forced messages were processed")
    
    # Return combined response
    combined_reply = "\n".join([msg.text for msg in messages])
    message_texts = [msg.text for msg in messages]
    return {
        "reply": message_texts[0] if len(message_texts) == 1 else combined_reply,
        "messages": message_texts,
        "next_node": current_node_id,
        "conversation_id": conversation_id
    }

@router.get("/{session_id}/history", response_model=SessionWithHistory)
def get_session_history(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return db_session