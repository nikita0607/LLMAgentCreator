from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.services.knowledge_service import KnowledgeService
from app.services.webhook import call_webhook
from app.services.elevenlabs_chat import chat_with_agent
from app.db import get_db
from sqlalchemy.orm import Session
import json
import re

# Import the new NodeOutput model
from app.models.node_output import NodeOutput


def save_node_output(agent_id: int, node_id: str, node_type: str, output_text: str):
    """Save node output to the database."""
    try:
        db: Session = next(get_db())
        node_output = NodeOutput(
            agent_id=agent_id,
            node_id=node_id,
            node_type=node_type,
            output_text=output_text
        )
        db.add(node_output)
        db.commit()
        db.refresh(node_output)
        print(f"Saved output for node {node_id} (type: {node_type})")
    except Exception as e:
        print(f"Error saving node output for node {node_id}: {str(e)}")
        # Rollback in case of error
        try:
            db.rollback()
        except:
            pass


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
    
    def get_display_text(self) -> str:
        """
        Get the display text for this node that can be referenced by other nodes.
        Each node type can override this method to provide specific text.
        """
        return self.text or f"{self.type.capitalize()} Node ({self.id})"
    
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
        print(f"[WaitForUserInputNode] Processing with user_input: {user_input}")
        # This node doesn't generate a reply, it just signals that we need user input
        # The actual user input will be saved in the session by the API layer
        result = {
            "reply": "",  # Empty reply as we're waiting for user input
            "next_node": self.next,
            "conversation_id": conversation_id,
            "save_last_user_input": user_input  # Save current user input for later nodes
        }
        print(f"[WaitForUserInputNode] Result: {result}")
        return result
    
    def get_display_text(self) -> str:
        """Get display text for wait for user input node."""
        return self.text or "Waiting for user input..."


class ForcedMessageNode(Node):
    """Node that sends a predefined message without waiting for user input."""
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None,
                nodes: Optional[Dict[str, 'Node']] = None) -> Dict[str, Any]:
        print(f"[ForcedMessageNode] Processing with user_input: {user_input}")
        print(f"[ForcedMessageNode] Last user input: {last_user_input}")
        # Use last_user_input if available for formatting
        context = last_user_input if last_user_input is not None else user_input
        
        # Check if we should reference text from another node
        reference_node_id = self.node_data.get('reference_node_id')
        if reference_node_id:
            # Try to get the referenced node's result from database
            try:
                # First, try to get the full output from the node_output table
                from app.db import get_db
                from sqlalchemy.orm import Session
                from app.models.node_output import NodeOutput
                
                db: Session = next(get_db())
                # Get the most recent output from the referenced node
                referenced_output = db.query(NodeOutput).filter(
                    NodeOutput.node_id == reference_node_id
                ).order_by(NodeOutput.created_at.desc()).first()
                
                if referenced_output:
                    reply = referenced_output.output_text
                else:
                    # Fallback to session messages if no node output found
                    # Get session_id from conversation_id if possible
                    session_id = None
                    if conversation_id:
                        try:
                            # Try to parse conversation_id as session_id
                            session_id = int(conversation_id)
                        except ValueError:
                            # If conversation_id is not a valid integer, we can't get session messages
                            pass
                    
                    if session_id:
                        # Get the latest message from the referenced node
                        from app.models.session_message import SessionMessage
                        
                        # Get the most recent message from the referenced node
                        referenced_message = db.query(SessionMessage).filter(
                            SessionMessage.session_id == session_id,
                            SessionMessage.node_id == reference_node_id
                        ).order_by(SessionMessage.created_at.desc()).first()
                        
                        if referenced_message:
                            reply = referenced_message.text
                        else:
                            # Fallback to display text if no message found
                            if nodes and reference_node_id in nodes:
                                referenced_node = nodes[reference_node_id]
                                reply = referenced_node.get_display_text()
                            else:
                                reply = f"Error: No result found for node {reference_node_id}"
                    else:
                        # Fallback to display text if no session_id
                        if nodes and reference_node_id in nodes:
                            referenced_node = nodes[reference_node_id]
                            reply = referenced_node.get_display_text()
                        else:
                            reply = f"Error: No result found for node {reference_node_id}"
            except Exception as e:
                reply = f"Error: Could not retrieve result from node {reference_node_id}: {str(e)}"
        else:
            # Use forced_text if available, otherwise fall back to text
            reply = self.node_data.get('forced_text', self.text)
            if context:
                reply = self.safe_format(reply, context)
        
        result = {
            "reply": reply,
            "next_node": self.next,
            "conversation_id": conversation_id
        }
        print(f"[ForcedMessageNode] Result: {result}")
        return result
    
    def get_display_text(self) -> str:
        """Get display text for forced message node."""
        reference_node_id = self.node_data.get('reference_node_id')
        if reference_node_id:
            return f"Reference to node: {reference_node_id}"
        return self.node_data.get('forced_text', self.text) or "Forced message"


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
        print(f"[WebhookNode] Extracting params with user_input: {user_input}")
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
        
        print(f"[WebhookNode] Found params: {found_params}")
        print(f"[WebhookNode] Missing params: {missing}")

        return found_params, missing, conversation_id
    
    def get_display_text(self) -> str:
        """Get display text for webhook node."""
        action = self.node_data.get("action", "webhook")
        return self.text or f"Webhook: {action}"
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        print(f"[WebhookNode] Processing with user_input: {user_input}")
        print(f"[WebhookNode] Last user input: {last_user_input}")
        # Webhook nodes should not depend on current user input
        # They work with last user input or no input
        context = last_user_input if last_user_input is not None else {}
        params = self.node_data.get("params", [])
        
        # Extract parameters via LLM
        found_params, missing, conversation_id = self.extract_params_via_llm(
            context or {}, params, system_prompt, voice_id, conversation_id
        )

        if missing:
            missing_message = self.node_data.get("missing_param_message", "Missing data")
            # Save the missing parameter message to the database
            save_node_output(self.agent_id, self.id, "webhook", missing_message)
            
            result = {
                "reply": missing_message,
                "action": {"name": self.node_data["action"], "missing_params": missing},
                "next_node": self.id,  # Stay on same node to retry
                "conversation_id": conversation_id
            }
            print(f"[WebhookNode] Result (missing params): {result}")
            return result

        try:
            result = call_webhook(self.node_data["url"], found_params)
            # Save webhook result in context for further use
            if context:
                context['result'] = result
            
            result_text = f"Webhook {self.node_data.get('action', 'call')} executed successfully: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}"
            
            # Save the full output to the database
            save_node_output(self.agent_id, self.id, "webhook", str(result))
            
            result = {
                "reply": result_text,
                "next_node": self.node_data.get("on_success"),
                "conversation_id": conversation_id
            }
            print(f"[WebhookNode] Result (success): {result}")
            return result
        except Exception as e:
            error_message = f"Error calling {self.node_data['action']}: {str(e)}"
            # Save the error message to the database
            save_node_output(self.agent_id, self.id, "webhook", error_message)
            
            result = {
                "reply": error_message,
                "next_node": self.node_data.get("on_failure"),
                "conversation_id": conversation_id
            }
            print(f"[WebhookNode] Result (error): {result}")
            return result


class ConditionalLLMNode(Node):
    """Node that uses LLM to choose between different branches based on conditions."""
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        print(f"[ConditionalLLMNode] Processing with user_input: {user_input}")
        print(f"[ConditionalLLMNode] Last user input: {last_user_input}")
        # Conditional LLM nodes should not depend on current user input
        # They work with last user input or no input
        context = last_user_input if last_user_input is not None else {}
        branches = self.node_data.get("branches", [])
        default_branch = self.node_data.get("default_branch")
        
        if not branches:
            result = {
                "reply": "Error: No conditional branches configured",
                "next_node": default_branch,
                "conversation_id": conversation_id
            }
            print(f"[ConditionalLLMNode] Result (no branches): {result}")
            return result
        
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
                
            result = {
                "reply": "",
                "next_node": next_node,
                "conversation_id": conversation_id
            }
            print(f"[ConditionalLLMNode] LLM response: {response}")
            print(f"[ConditionalLLMNode] Choice: {choice}")
            print(f"[ConditionalLLMNode] Result: {result}")
            return result
            
        except Exception as e:
            result = {
                "reply": "",
                "next_node": default_branch,
                "conversation_id": conversation_id
            }
            print(f"[ConditionalLLMNode] Result (error): {result}")
            return result
    
    def get_display_text(self) -> str:
        """Get display text for conditional LLM node."""
        return self.text or "Conditional LLM Node"


class KnowledgeNode(Node):
    """Node that retrieves information from knowledge sources."""
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        print(f"[KnowledgeNode] Processing with user_input: {user_input}")
        print(f"[KnowledgeNode] Last user input: {last_user_input}")
        # Knowledge nodes don't process anything directly, they just provide context to connected nodes
        # The actual knowledge retrieval happens in the LLMRequestNode when it gets connected knowledge context
        
        # Save information about this knowledge node to the database
        try:
            from app.db import get_db
            from sqlalchemy.orm import Session
            from app.services.knowledge_service import KnowledgeService
            import re
            
            db: Session = next(get_db())
            service = KnowledgeService(db)
            
            # Get knowledge source information
            source_info = service.get_source_info(self.agent_id, self.id)
            
            # If no source info found, check if node text contains a URL
            if not source_info and self.text:
                # Check if the node text is a valid URL
                url_pattern = re.compile(
                    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                )
                url_match = url_pattern.match(self.text.strip())
                
                if url_match:
                    # If node text is a URL, treat it as a web source
                    url = url_match.group(0)
                    knowledge_text = f"Knowledge source: web\nURL: {url}"
                    
                    # Try to add this URL to the knowledge service
                    try:
                        service.add_url(
                            agent_id=self.agent_id,
                            node_id=self.id,
                            url=url,
                            url_metadata={"description": f"URL from node text: {url}"}
                        )
                        knowledge_text += "\n[URL automatically registered from node text]"
                    except Exception as e:
                        knowledge_text += f"\n[Warning: Could not register URL automatically: {str(e)}]"
                else:
                    knowledge_text = f"Knowledge node without source information\nNode text: {self.text}"
            elif source_info:
                knowledge_text = f"Knowledge source: {source_info.get('source_type', 'unknown')}"
                if source_info.get("source_data") and "url" in source_info["source_data"]:
                    knowledge_text += f"\nURL: {source_info['source_data']['url']}"
                if source_info.get("extractor_metadata"):
                    text_content = source_info["extractor_metadata"].get("text_content", "")
                    if text_content:
                        knowledge_text += f"\nContent: {text_content[:500]}..." if len(text_content) > 500 else f"\nContent: {text_content}"
            else:
                knowledge_text = "Knowledge node without source information"
                
            # Save the knowledge information to the database
            save_node_output(self.agent_id, self.id, "knowledge", knowledge_text)
        except Exception as e:
            error_message = f"Error processing knowledge node: {str(e)}"
            save_node_output(self.agent_id, self.id, "knowledge", error_message)
        
        result = {
            "reply": "",  # Empty reply as knowledge nodes don't display anything
            "next_node": self.next,
            "conversation_id": conversation_id
        }
        print(f"[KnowledgeNode] Result: {result}")
        return result
    
    def get_display_text(self) -> str:
        """Get display text for knowledge node - should be empty as knowledge nodes don't display text."""
        return ""


class LLMRequestNode(Node):
    """Node that makes an LLM request considering conversation history, last user input, and knowledge context."""
    
    def _get_conversation_history(self, session_id: Optional[int], db: Session, max_history: int = 5) -> str:
        """Retrieve conversation history from the database."""
        if not session_id:
            return ""
        
        try:
            # Get session messages ordered by creation time
            from app.models.session_message import SessionMessage
            messages = db.query(SessionMessage).filter(
                SessionMessage.session_id == session_id
            ).order_by(SessionMessage.created_at.desc()).limit(max_history * 2).all()  # Get more to ensure we have enough
            
            # Format messages in chronological order
            history_lines = []
            for msg in reversed(messages):  # Reverse to get chronological order
                role = "User" if msg.sender == "user" else "Assistant"
                history_lines.append(f"{role}: {msg.text}")
            
            return "\n".join(history_lines)
        except Exception as e:
            print(f"Error retrieving conversation history: {str(e)}")
            return ""
    
    def _get_connected_nodes_context(self, db: Session) -> str:
        """Retrieve context from connected nodes by fetching their outputs from the database."""
        context = ""
        
        # Get connected nodes from node_data
        connected_knowledge_nodes = self.node_data.get("connected_knowledge_nodes", [])
        connected_webhook_nodes = self.node_data.get("connected_webhook_nodes", [])
        connected_nodes = connected_knowledge_nodes + connected_webhook_nodes
        
        for node_id in connected_nodes:
            try:
                # Get the most recent output from the connected node
                from app.models.node_output import NodeOutput
                
                # Get the most recent output from the connected node
                node_output = db.query(NodeOutput).filter(
                    NodeOutput.node_id == node_id
                ).order_by(NodeOutput.created_at.desc()).first()
                
                if node_output:
                    context += f"Context from node {node_id}:\n{node_output.output_text}\n\n"
                else:
                    # If no node output found, check if it's a knowledge node and try to get its source
                    try:
                        from app.services.knowledge_service import KnowledgeService
                        service = KnowledgeService(db)
                        
                        # Get knowledge source information
                        source_info = service.get_source_info(self.agent_id, node_id)
                        
                        if source_info:
                            if source_info.get("source_type") == "web" and source_info.get("source_data", {}).get("url"):
                                # For web sources, perform actual scraping
                                url = source_info["source_data"]["url"]
                                try:
                                    results = service.scrape_and_search_web_source(self.agent_id, node_id, "relevant information", top_k=3)
                                    if results:
                                        context += f"Context from web node {node_id} ({url}):\n"
                                        for result in results:
                                            context += f"{result[1]}\n"  # result[1] contains the text
                                        context += "\n"
                                    else:
                                        context += f"Context from web node {node_id} ({url}): [No content extracted]\n\n"
                                except Exception as scrape_error:
                                    context += f"Context from web node {node_id} ({url}): [Error scraping: {str(scrape_error)}]\n\n"
                            else:
                                # For other sources, use the extractor metadata
                                if source_info.get("extractor_metadata"):
                                    text_content = source_info["extractor_metadata"].get("text_content", "")
                                    if text_content:
                                        context += f"Context from node {node_id}:\n{text_content[:1000]}\n\n"  # First 1000 chars
                                    else:
                                        context += f"Context from node {node_id}: [No text content available]\n\n"
                                else:
                                    context += f"Context from node {node_id}: [No content available]\n\n"
                        else:
                            # If no source info found, try to get from session messages
                            # This is a fallback for nodes that don't save to node_output table
                            context += f"Context from node {node_id}: [No output found]\n\n"
                    except Exception as source_error:
                        print(f"Error retrieving source info from node {node_id}: {str(source_error)}")
                        context += f"Context from node {node_id}: [Error retrieving source info]\n\n"
                    
            except Exception as e:
                print(f"Error retrieving context from node {node_id}: {str(e)}")
                context += f"Context from node {node_id}: [Error retrieving output]\n\n"
        
        return context
    
    def process(self, user_input: Optional[Dict[str, Any]] = None, 
                system_prompt: str = "", voice_id: str = "", 
                conversation_id: Optional[str] = None,
                last_user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        print(f"[LLMRequestNode] Processing with user_input: {user_input}")
        print(f"[LLMRequestNode] Last user input: {last_user_input}")
        print(f"[LLMRequestNode] System prompt: {system_prompt}")
        print(f"[LLMRequestNode] Voice ID: {voice_id}")
        print(f"[LLMRequestNode] Conversation ID: {conversation_id}")
        
        from app.db import get_db
        from sqlalchemy.orm import Session
        from app.models.session_message import SessionMessage
        from app.models.session import Session as SessionModel
        
        db: Session = next(get_db())
        
        # LLM Request nodes should not depend on current user input
        # They work with conversation history and connected context
        user_text = ""
        
        # Get session_id from conversation_id if possible
        session_id = None
        if conversation_id:
            try:
                # Try to parse conversation_id as session_id
                session_id = int(conversation_id)
            except ValueError:
                # If conversation_id is not a valid integer, try to find session by conversation_id
                session = db.query(SessionModel).filter(SessionModel.conversation_id == conversation_id).first()
                if session:
                    session_id = session.id
        
        # Get conversation history
        # conversation_history = self._get_conversation_history(session_id, db)
        # print(f"[LLMRequestNode] Conversation history: {conversation_history}")
        
        # Get context from connected nodes
        connected_nodes_context = self._get_connected_nodes_context(db)
        print(f"[LLMRequestNode] Connected nodes context: {connected_nodes_context}")
        
        # Build the complete prompt for the LLM
        prompt_parts = []
        
        # Add system prompt if available
        if self.node_data.get("system_prompt"):
            prompt_parts.append(f"System: {self.node_data.get('system_prompt')}")
        elif system_prompt:
            prompt_parts.append(f"System: {system_prompt}")
        
        # Add conversation history if available
        # if conversation_history:
            # prompt_parts.append(f"Conversation History:\n{conversation_history}")
        
        # Add context from connected nodes if available
        if connected_nodes_context:
            prompt_parts.append(f"Node Context:\n{connected_nodes_context}")
        
        # LLM Request nodes generate responses based on context, not current user input
        prompt_parts.append("Assistant: Please provide a helpful response based on the context above.")
        
        full_prompt = "\n\n".join(prompt_parts)
        print(f"[LLMRequestNode] Full prompt: {full_prompt}")
        
        try:
            # Make the LLM request
            response = chat_with_agent(full_prompt, voice_id, conversation_id)
            conversation_id = response.get("conversation_id")
            reply = response.get("reply", "")
            
            # Save the full output to the database
            save_node_output(self.agent_id, self.id, "llm_request", reply)
            
            # Modified: LLM Request nodes should not output any message directly
            # Only store the result for potential reference by other nodes
            result = {
                "reply": "",  # Empty reply - no message should be displayed
                "next_node": self.next,
                "conversation_id": conversation_id
            }
            print(f"[LLMRequestNode] LLM response: {response}")
            print(f"[LLMRequestNode] Result: {result}")
            return result
            
        except Exception as e:
            error_message = f"Error processing LLM request: {str(e)}"
            # Save the error message to the database
            save_node_output(self.agent_id, self.id, "llm_request", error_message)
            
            # Modified: LLM Request nodes should not output any message directly, even in error cases
            result = {
                "reply": "",  # Empty reply - no message should be displayed
                "next_node": self.next,
                "conversation_id": conversation_id
            }
            print(f"[LLMRequestNode] Result (error): {result}")
            return result
    
    def get_display_text(self) -> str:
        """Get display text for LLM request node."""
        system_prompt = self.node_data.get("system_prompt", "")
        if system_prompt:
            # Return first 50 characters of system prompt as display text
            return system_prompt[:50] + ("..." if len(system_prompt) > 50 else "")
        return self.text or "LLM Request Node"


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
    elif node_type == "llm_request":
        return LLMRequestNode(node_data, agent_id)
    else:
        raise ValueError(f"Unknown node type: {node_type}")