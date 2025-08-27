from app.core.config import settings

from pydantic import BaseModel
from typing import Optional, Callable
from groq import Groq
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
groq_client = Groq(api_key=settings.GROQ_API_KEY)

class MessageOut(BaseModel):
    reply: str
    conversation_id: str
    actions: Optional[list] = []

def chat_with_agent(prompt: str, voice_id, conversation_id: Optional[str] = None):
    """
    Отправка сообщения в Groq LLM (LLaMA 3.1) и получение ответа.
    conversation_id пока можно игнорировать — Groq не хранит контексты на сервере.
    Если нужна "память", надо хранить историю сообщений у себя.
    """

    # Здесь можно хранить историю чата у себя (например, в БД), но для примера просто одно сообщение
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",  # можно заменить на любую другую доступную
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