from typing import Optional, Dict, Any, List

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


def get_connected_nodes(nodes: dict[str, dict], edges: List[dict], node_id: str) -> Dict[str, List[str]]:
    """Get connected nodes of specific types for a given node."""
    connected = {
        "knowledge_nodes": [],
        "webhook_nodes": []
    }
    
    # Find all edges that target this node
    incoming_edges = [edge for edge in edges if edge.get("target") == node_id]
    
    # For each incoming edge, find the source node and check its type
    for edge in incoming_edges:
        source_id = edge.get("source")
        if source_id and source_id in nodes:
            source_node = nodes[source_id]
            node_type = source_node.get("type")
            
            if node_type == "knowledge":
                connected["knowledge_nodes"].append(source_id)
            elif node_type == "webhook":
                connected["webhook_nodes"].append(source_id)
    
    return connected


def process_node(nodes: dict[str, dict], node: dict, agent_id: int, user_input: Optional[dict[str]] = None,
                 system_prompt: str = "", voice_id: str = "", conversation_id: Optional[str] = None,
                 last_user_input: Optional[Dict[str, Any]] = None, edges: List[dict] = None):
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
    node_id = node.get('id')
    node_type = node.get('type')
    print(f"=== PROCESSING NODE ===")
    print(f"Node ID: {node_id}")
    print(f"Node Type: {node_type}")
    print(f"User Input Provided: {user_input is not None}")
    print(f"Last User Input Available: {last_user_input is not None}")
    print(f"NODE DATA: {node}")
    print("========================")
    
    try:
        # Create a copy of the node data to avoid modifying the original
        node_data = node.copy()
        
        # If this is an LLM Request node, add information about connected nodes
        if node.get("type") == "llm_request" and edges:
            connected_nodes = get_connected_nodes(nodes, edges, node.get("id"))
            node_data["connected_knowledge_nodes"] = connected_nodes["knowledge_nodes"]
            node_data["connected_webhook_nodes"] = connected_nodes["webhook_nodes"]
            print(f"LLM Request node connected to knowledge nodes: {connected_nodes['knowledge_nodes']}")
            print(f"LLM Request node connected to webhook nodes: {connected_nodes['webhook_nodes']}")
        
        # Create the appropriate node object based on type
        node_obj = create_node(node_data, agent_id)
        
        # Process the node using the OOP approach
        # Only pass user_input to nodes that actually need it
        if node.get("type") == "wait_for_user_input":
            # Only wait_for_user_input node should receive user input
            print(f"Processing WAIT_FOR_USER_INPUT node with actual user input")
            result = node_obj.process(
                user_input=user_input,
                system_prompt=system_prompt,
                voice_id=voice_id,
                conversation_id=conversation_id,
                last_user_input=last_user_input
            )
        elif node.get("type") == "forced_message":
            # Pass nodes dictionary to ForcedMessageNode for reference resolution
            print(f"Processing FORCED_MESSAGE node")
            result = node_obj.process(
                user_input=None,  # No user input for automatic nodes
                system_prompt=system_prompt,
                voice_id=voice_id,
                conversation_id=conversation_id,
                last_user_input=last_user_input,
                nodes=nodes  # Pass nodes for reference resolution
            )
        else:
            # All other nodes don't need user input and should process automatically
            print(f"Processing {node_type.upper()} node automatically (no user input)")
            result = node_obj.process(
                user_input=None,  # No user input for automatic nodes
                system_prompt=system_prompt,
                voice_id=voice_id,
                conversation_id=conversation_id,
                last_user_input=last_user_input
            )
        
        # Ensure action is included in result if it exists
        if "action" not in result:
            result["action"] = node.get("action")
            
        print(f"Node result: {result}")
        print(f"Next node: {result.get('next_node')}")
        print("========================")
        return result
        
    except Exception as e:
        print(f"Error processing node {node.get('id')}: {str(e)}")
        return {
            "reply": f"Error processing node: {str(e)}",
            "next_node": None,
            "conversation_id": conversation_id
        }