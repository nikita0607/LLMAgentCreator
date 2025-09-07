import openai
from app.core.config import settings

from pydantic import BaseModel
from typing import Optional, Callable
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ConversationInitiationData, AudioInterface

class DummyAudioInterface(AudioInterface):
    def output(self, audio: bytes): ...
    def interrupt(self): ...
    def start(self, input_callback: Callable[[bytes], None]): ...
    def stop(self): ...
    def play(self, audio_chunk): ...
    def close(self): ...


# Инициализация клиента ElevenLabs
client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

# Инициализация клиента OpenRouter
# Use a minimal configuration to avoid version conflicts
openrouter_client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
    timeout=30.0,
    max_retries=2
)

class MessageOut(BaseModel):
    reply: str
    conversation_id: str
    actions: Optional[list] = []

def chat_with_agent(prompt: str, voice_id, conversation_id: Optional[str] = None):
    """
    Отправка сообщения в OpenRouter LLM и получение ответа.
    conversation_id пока можно игнорировать — OpenRouter не хранит контексты на сервере.
    Если нужна "память", надо хранить историю сообщений у себя.
    """

    # Здесь можно хранить историю чата у себя (например, в БД), но для примера просто одно сообщение
    response = openrouter_client.chat.completions.create(
        model="deepseek/deepseek-chat-v3.1:free",  # можно заменить на любую другую доступную модель
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    reply = response.choices[0].message.content
    print(prompt, reply)

    return {
        "reply": reply,
        "conversation_id": conversation_id or "local-memory",  # если надо, можно сделать UUID
    }