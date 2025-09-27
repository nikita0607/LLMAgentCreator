import json
from typing import Optional

from app.services.knowledge_service import KnowledgeService
from app.services.webhook import call_webhook
from app.services.elevenlabs_chat import chat_with_agent

from app.db import get_db
from sqlalchemy.orm import Session


import re

def safe_format(template: str, context: dict) -> str:
    """
    Форматирует строку с поддержкой вложенных ключей через точку или ['ключ'].
    Пример: "Ответ: {result.value}" или "Ответ: {result['value']}".
    """
    def get_value(path: str, ctx: dict):
        # удаляем кавычки и скобки
        parts = re.split(r"[.\[\]']", path)
        parts = [p for p in parts if p]  # убираем пустые
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


def extract_params_via_llm(user_input: dict[str], params: dict, system_prompt: str, voice_id: str, conversation_id: Optional[str] = None):
    """
    Используем LLM для извлечения параметров из текста пользователя.
    params: {
        "param_name": {
            "values": {
                "description": "...",
                "value": "..." (опционально, фиксированное значение)
            }
        }
    }

    Возвращает:
        - found_params: dict найденных параметров (включая фиксированные)
        - missing: список недостающих
        - conversation_id: актуальный ID разговора
    """
    if not params:
        return {}, [], conversation_id

    # фиксированные и динамические параметры
    fixed_params = {p['name']: {'value': p['value'], 'description': p['description']} for p in params if "value" in p and p['value']}
    dynamic_params = {p['name']: {'description': p['description']} for p in params if "value" not in p or not p['value']}

    # формируем описание для LLM
    param_descriptions = "\n".join([f"- {name}: {desc['description']}" for name, desc in dynamic_params.items()])

    if dynamic_params:
        prompt = (
            f"{system_prompt}\n"
            f"Ввод пользователя: '{user_input.get('user_text')}'\n"
            f"Извлеки значения для следующих параметров:\n{param_descriptions}\n"
            f"Верни JSON с найденными параметрами в формате 'PARAM_NAME': 'PARAM_VALUE'. Если параметр не найден — пропусти его. В ответ не отправляй ничего кроме самого JSON. "
            f"Не используй оформлений"
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

    # объединяем найденные и фиксированные
    found_params = {**fixed_params, **found_dynamic}

    # определяем отсутствующие (только для динамических)
    missing = [k for k in dynamic_params.keys() if k not in found_dynamic]

    return found_params, missing, conversation_id


def get_node(nodes: dict[str, dict], node_id):
    """Get node by ID from nodes dictionary."""
    if node_id is None:
        return None
    return nodes.get(node_id)


def process_node(nodes: dict[str, dict], node: dict, agent_id: int, user_input: Optional[dict[str]] = None,
                 system_prompt: str = "", voice_id: str = "", conversation_id: Optional[str] = None):
    """
    Processes drag&drop node (message / webhook) and returns:
    {
        reply: str,
        action: Optional[dict],
        next_node: Optional[str],
        conversation_id: Optional[str]
    }
    
    Allows infinite loops for continuous conversation with agents.
    """
    print(f"PROCESSING NODE: {node.get('id')} of type: {node.get('type')}")
    print(f"NODE DATA: {node}")
    
    if node["type"] == "message":
        reply: str = node['text']
        reply = safe_format(reply, user_input)
        print(f"Message reply: {reply}")
        return {
            "reply": reply,
            "next_node": node.get("next"),
            "conversation_id": conversation_id
        }

    if node["type"] == "forced_message":
        # Forced message node sends predefined text without waiting for user input
        reply: str = node.get('forced_text', node.get('text', 'Forced message'))
        reply = safe_format(reply, user_input)
        print(f"Forced message reply: {reply}")
        return {
            "reply": reply,
            "next_node": node.get("next"),
            "conversation_id": conversation_id
        }

    if node["type"] == "webhook":
        params = node.get("params", {})

        # извлекаем параметры через LLM
        found_params, missing, conversation_id = extract_params_via_llm(
            user_input, params, system_prompt, voice_id, conversation_id
        )

        if missing:
            return {
                "reply": node.get("missing_param_message", None) or  "Не хватает данных",
                "action": {"name": node["action"], "missing_params": missing},
                "next_node": node["id"],
                "conversation_id": conversation_id
            }

        try:
            result = call_webhook(node["url"], found_params)
            # Сохраняем результат webhook в user_input для дальнейшего использования
            if user_input:
                user_input['result'] = result
            
            return {
                "reply": f"Webhook {node.get('action', 'call')} executed successfully: {str(result)[:200]}{'...' if len(str(result)) > 200 else ''}",
                "next_node": node.get("on_success"),
                "conversation_id": conversation_id
            }
        except Exception as e:
            return {
                "reply": f"Ошибка вызова {node['action']}: {str(e)}",
                "next_node": node.get("on_failure"),
                "conversation_id": conversation_id
            }

    if node["type"] == "conditional_llm":
        # Обрабатываем условное ветвление через LLM
        branches = node.get("branches", [])
        default_branch = node.get("default_branch")
        
        if not branches:
            return {
                "reply": "Ошибка: не настроены условные ветки",
                "next_node": default_branch,
                "conversation_id": conversation_id
            }
        
        # Формируем промпт для LLM для выбора подходящей ветки
        user_text = user_input.get("user_text", "")
        conditions_text = "\n".join([f"{i+1}. {branch['condition_text']}" 
                                    for i, branch in enumerate(branches)])
        
        llm_prompt = (
            f"{system_prompt}\n"
            f"Пользователь сказал: '{user_text}'\n"
            f"Выбери наиболее подходящий вариант из следующих условий:\n{conditions_text}\n"
            f"Ответь только номером варианта (1-{len(branches)}) без дополнительных пояснений. "
            f"Если ни один вариант не подходит, ответь 0."
        )
        
        try:
            response = chat_with_agent(llm_prompt, voice_id, conversation_id)
            conversation_id = response.get("conversation_id")
            
            # Парсим ответ LLM
            choice = response.get("reply", "0").strip()
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(branches):
                    selected_branch = branches[choice_num - 1]
                    next_node = selected_branch.get("next_node")
                else:
                    # Выбран несуществующий вариант или 0 (нет подходящего)
                    next_node = default_branch
            except ValueError:
                # LLM вернул не число
                next_node = default_branch
                
            return {
                "reply": f"Выбрано условие: {branches[choice_num-1]['condition_text'] if 1 <= choice_num <= len(branches) else 'по умолчанию'}",
                "next_node": next_node,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            return {
                "reply": f"Ошибка при обработке условного ветвления: {str(e)}",
                "next_node": default_branch,
                "conversation_id": conversation_id
            }

    if node["type"] == "knowledge":
        db: Session = next(get_db())
        service = KnowledgeService(db)

        query = user_input["user_text"]
        node_id = node["id"]

        # Проверяем тип источника знаний
        source_info = service.get_source_info(agent_id, node_id)
        
        if source_info and source_info.get("source_type") == "web":
            # Для веб-источников выполняем реальный скрапинг
            results = service.scrape_and_search_web_source(agent_id, node_id, query, top_k=5)
            print(results)
        else:
            # Для других источников используем стандартный поиск по embeddings
            results = service.search_embeddings(agent_id, node_id, query, top_k=5)

        reply = ""
        for embedding in results:
            reply += f"{embedding[1]}\n"  # embedding[1] содержит текст

        return {
            "reply": reply.strip(),
            "next_node": node.get("next"),
            "conversation_id": conversation_id
        }


    return None