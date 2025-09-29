from typing import Optional, Dict, Any

# Remove the old imports that are now in the Node classes
# from app.services.knowledge_service import KnowledgeService
# from app.services.webhook import call_webhook
# from app.services.elevenlabs_chat import chat_with_agent

# Import our new Node classes
from app.services.node import create_node


def get_node(nodes: dict[str, dict], node_id):
    """Get node by ID from nodes dictionary."""
    if node_id is None:
        return None
    return nodes.get(node_id)


def process_node(nodes: dict[str, dict], node: dict, agent_id: int, user_input: Optional[dict[str]] = None,
                 system_prompt: str = "", voice_id: str = "", conversation_id: Optional[str] = None,
                 last_user_input: Optional[Dict[str, Any]] = None):
    """
    Processes drag&drop node (message / webhook) using the new Node OOP approach and returns:
    {
        reply: str,
        action: Optional[dict],
        next_node: Optional[str],
        conversation_id: Optional[str],
        save_last_user_input: Optional[dict]  # New field for saving user input
    }
    
    Allows infinite loops for continuous conversation with agents.
    """
    print(f"PROCESSING NODE: {node.get('id')} of type: {node.get('type')}")
    print(f"NODE DATA: {node}")
    
    try:
        # Create the appropriate node object based on type
        node_obj = create_node(node, agent_id)
        
        # Process the node using the OOP approach
        result = node_obj.process(
            user_input=user_input,
            system_prompt=system_prompt,
            voice_id=voice_id,
            conversation_id=conversation_id,
            last_user_input=last_user_input
        )
        
        # Ensure action is included in result if it exists
        if "action" not in result:
            result["action"] = node.get("action")
            
        print(f"Node result: {result}")
        return result
        
    except Exception as e:
        print(f"Error processing node {node.get('id')}: {str(e)}")
        return {
            "reply": f"Error processing node: {str(e)}",
            "next_node": None,
            "conversation_id": conversation_id
        }