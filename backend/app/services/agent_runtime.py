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
            f"Верни JSON с найденными параметрами в формате 'PARAM_NAME': 'PARAM_VALUE'. Если параметр не найден — пропусти его. В ответ не отправляй ничего кроме самого валидного JSON. "
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
    for n_id in nodes:
        if n_id == node_id:
            return nodes[n_id]
        return None
    return None


def process_node(
    nodes: dict[str, dict],
    node: dict,
    agent_id: int,
    user_input: Optional[dict[str]] = None,
    system_prompt: str = "",
    voice_id: str = "",
    conversation_id: Optional[str] = None,
):
    """
    Обрабатывает узел drag&drop (message / webhook) и возвращает:
    {
        reply: str,
        action: Optional[dict],
        next_node: Optional[str],
        conversation_id: Optional[str]
    }
    """
    print("HERE", node)
    if node["type"] == "message":
        reply: str = node['text']
        reply = safe_format(reply, user_input)
        print(reply)
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
            next_node = get_node(nodes, node.get("on_success"))
            print("ASDASD", user_input)
            user_input['result'] = result
            next_call = process_node(
                nodes=nodes,
                node=next_node,
                agent_id=agent_id,
                user_input=user_input,
                system_prompt=system_prompt,
                voice_id=voice_id,
                conversation_id=conversation_id,
            )

            return next_call
        except Exception as e:
            return {
                "reply": f"Ошибка вызова {node['action']}: {str(e)}",
                "next_node": node.get("on_failure"),
                "conversation_id": conversation_id
            }

    if node["type"] == "knowledge":
        db: Session = next(get_db())
        service = KnowledgeService(db)

        query = user_input["user_text"]
        node_id = node["id"]

        results = service.search_embeddings(agent_id, node_id, query, top_k=5)

        reply = ""
        for embedding in results:
            reply += f"{embedding}\n"

        return {
            "reply": reply.strip(),
            "next_node": node.get("next"),
            "conversation_id": conversation_id
        }


    return None