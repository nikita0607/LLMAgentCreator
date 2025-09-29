from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from app.services.knowledge_service import KnowledgeService
from app.services.webhook import call_webhook
from app.services.elevenlabs_chat import chat_with_agent
from app.db import get_db
from sqlalchemy.orm import Session
import json
import re


class Node(ABC):
    """Base class for all node types in the agent logic flow."""
    
    def __init__(self, node_data: Dict[str, Any], agent_id: int):
        self.id = node_data.get("id")
        self.type = node_data.get("type")
        self.next = node_data.get("next")
        self.text = node_data.get("text", "")
        self.agent_id = agent_id
        self.node_data = node_data  # Store raw data for subclasses
    
    @abstractmethod
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process the node and return a result dictionary with:
        - reply: str - the response text
        - next_node: Optional[str] - the ID of the next node to process
        - conversation_id: Optional[str] - updated conversation ID
        - action: Optional[Dict] - any action data to be stored
        - save_last_user_input: Optional[Dict] - user input to save for later use
        """
        pass
    
    def safe_format(self, template: str, context: dict) -> str:
        """
        Format a string with support for nested keys via dot notation or ['key'].
        Example: "Answer: {result.value}" or "Answer: {result['value']}".
        """
        def get_value(path: str, ctx: dict):
            # Remove quotes and brackets
            parts = re.split(r"[.\[\]']", path)
            parts = [p for p in parts if p]  # Remove empty
            value = ctx
            for p in parts:
                if isinstance(value, dict):
                    value = value.get(p, f"<missing:{p}>")
                else:
                    return f"<invalid:{p}>"
            return value

        def replacer(match):
            expr = match.group(1).strip()
            return str(get_value(expr, context))

        return re.sub(r"{([^{}]+)}", replacer, template)


class WaitForUserInputNode(Node):
    """Node that waits for user input and saves it for later use."""
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # This node doesn't generate a reply, it just signals that we need user input
        # The actual user input will be saved in the session by the API layer
        return {
            "reply": "",  # Empty reply as we're waiting for user input
            "next_node": self.next,
            "conversation_id": conversation_id,
            "save_last_user_input": user_input  # Save current user input for later nodes
        }


class ForcedMessageNode(Node):
    """Node that sends a predefined message without waiting for user input."""
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Use last_user_input if available for formatting
        context = last_user_input if last_user_input is not None else user_input
        # Use forced_text if available, otherwise fall back to text
        reply = self.node_data.get('forced_text', self.text)
        if context:
            reply = self.safe_format(reply, context)
        
        return {
            "reply": reply,
            "next_node": self.next,
            "conversation_id": conversation_id
        }


class WebhookNode(Node):
    """Node that calls a webhook with extracted parameters."""
    
    def extract_params_via_llm(self, user_input: dict[str], params: dict, system_prompt: str, 
                               voice_id: str, conversation_id: Optional[str] = None):
        """
        Use LLM to extract parameters from user text.
        params: {
            "param_name": {
                "values": {
                    "description": "...",
                    "value": "..." (optional, fixed value)
                }
            }
        }

        Returns:
            - found_params: dict of found parameters (including fixed ones)
            - missing: list of missing parameters
            - conversation_id: updated conversation ID
        """
        if not params:
            return {}, [], conversation_id

        # Fixed and dynamic parameters
        fixed_params = {p['name']: {'value': p['value'], 'description': p['description']} 
                       for p in params if "value" in p and p['value']}
        dynamic_params = {p['name']: {'description': p['description']} 
                         for p in params if "value" not in p or not p['value']}

        # Format description for LLM
        param_descriptions = "\n".join([f"- {name}: {desc['description']}" 
                                       for name, desc in dynamic_params.items()])

        if dynamic_params:
            prompt = (
                f"{system_prompt}\n"
                f"User input: '{user_input.get('user_text')}'\n"
                f"Extract values for the following parameters:\n{param_descriptions}\n"
                f"Return JSON with found parameters in format 'PARAM_NAME': 'PARAM_VALUE'. "
                f"If a parameter is not found, skip it. Return only the JSON without any formatting."
            )

            response = chat_with_agent(prompt, voice_id, conversation_id)
            conversation_id = response.get("conversation_id")

            try:
                found_dynamic = json.loads(response.get("reply", "{}"))
                found_dynamic = {k: v for k, v in found_dynamic.items() if v is not None}
            except Exception:
                found_dynamic = {}
        else:
            found_dynamic = {}

        # Combine found and fixed parameters
        found_params = {**fixed_params, **found_dynamic}

        # Determine missing (only for dynamic parameters)
        missing = [k for k in dynamic_params.keys() if k not in found_dynamic]

        return found_params, missing, conversation_id
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Use last_user_input if available
        context = last_user_input if last_user_input is not None else user_input
        params = self.node_data.get("params", [])
        
        # Extract parameters via LLM
        found_params, missing, conversation_id = self.extract_params_via_llm(
            context or {}, params, system_prompt, voice_id, conversation_id
        )

        if missing:
            return {
                "reply": self.node_data.get("missing_param_message", "Missing data"),
                "action": {"name": self.node_data["action"], "missing_params": missing},
                "next_node": self.id,  # Stay on same node to retry
                "conversation_id": conversation_id
            }

        try:
            result = call_webhook(self.node_data["url"], found_params)
            # Save webhook result in context for further use
            if context:
                context['result'] = result
            
            return {
                "reply": f"Webhook {self.node_data.get('action', 'call')} executed successfully: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}",
                "next_node": self.node_data.get("on_success"),
                "conversation_id": conversation_id
            }
        except Exception as e:
            return {
                "reply": f"Error calling {self.node_data['action']}: {str(e)}",
                "next_node": self.node_data.get("on_failure"),
                "conversation_id": conversation_id
            }


class ConditionalLLMNode(Node):
    """Node that uses LLM to choose between different branches based on conditions."""
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Use last_user_input if available
        context = last_user_input if last_user_input is not None else user_input
        branches = self.node_data.get("branches", [])
        default_branch = self.node_data.get("default_branch")
        
        if not branches:
            return {
                "reply": "Error: No conditional branches configured",
                "next_node": default_branch,
                "conversation_id": conversation_id
            }
        
        # Format prompt for LLM to choose branch
        user_text = context.get("user_text", "") if context else ""
        conditions_text = "\n".join([f"{i+1}. {branch['condition_text']}" 
                                    for i, branch in enumerate(branches)])
        
        llm_prompt = (
            f"{system_prompt}\n"
            f"User said: '{user_text}'\n"
            f"Choose the most appropriate option from the following conditions:\n{conditions_text}\n"
            f"Respond only with the option number (1-{len(branches)}) without additional explanations. "
            f"If none match, respond with 0."
        )
        
        try:
            response = chat_with_agent(llm_prompt, voice_id, conversation_id)
            conversation_id = response.get("conversation_id")
            
            # Parse LLM response
            choice = response.get("reply", "0").strip()
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(branches):
                    selected_branch = branches[choice_num - 1]
                    next_node = selected_branch.get("next_node")
                else:
                    # Invalid choice or 0 (no match)
                    next_node = default_branch
            except ValueError:
                # LLM returned non-numeric response
                next_node = default_branch
                
            return {
                "reply": "",
                "next_node": next_node,
                "conversation_id": conversation_id
            }
            
        except Exception:
            return {
                "reply": "",
                "next_node": default_branch,
                "conversation_id": conversation_id
            }


class KnowledgeNode(Node):
    """Node that retrieves information from knowledge sources."""
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        db: Session = next(get_db())
        service = KnowledgeService(db)

        # Use last_user_input if available
        context = last_user_input if last_user_input is not None else user_input
        query = context.get("user_text", "") if context else ""
        node_id = self.id

        # Check knowledge source type
        source_info = service.get_source_info(self.agent_id, node_id)
        
        if source_info and source_info.get("source_type") == "web":
            # For web sources, perform actual scraping
            results = service.scrape_and_search_web_source(self.agent_id, node_id, query, top_k=5)
        else:
            # For other sources, use standard embedding search
            results = service.search_embeddings(self.agent_id, node_id, query, top_k=5)

        reply = ""
        for embedding in results:
            reply += f"{embedding[1]}\n"  # embedding[1] contains the text

        return {
            "reply": reply.strip(),
            "next_node": self.next,
            "conversation_id": conversation_id
        }


def create_node(node_data: Dict[str, Any], agent_id: int) -> Node:
    """Factory function to create the appropriate node type based on node data."""
    node_type = node_data.get("type")
    
    if node_type == "wait_for_user_input":
        return WaitForUserInputNode(node_data, agent_id)
    elif node_type == "forced_message":
        return ForcedMessageNode(node_data, agent_id)
    elif node_type == "webhook":
        return WebhookNode(node_data, agent_id)
    elif node_type == "conditional_llm":
        return ConditionalLLMNode(node_data, agent_id)
    elif node_type == "knowledge":
        return KnowledgeNode(node_data, agent_id)
    else:
        raise ValueError(f"Unknown node type: {node_type}")