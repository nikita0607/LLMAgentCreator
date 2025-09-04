"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

interface Message {
  sender: "user" | "agent";
  text: string;
}

export default function ChatPage() {
  const params = useParams();
  const agentId = Number(params.id);

  const [agentName, setAgentName] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Загружаем агента и восстанавливаем/создаём сессию
  useEffect(() => {
    async function initChat() {
      try {
        const agent = await apiFetch(`/agents/${agentId}`);
        setAgentName(agent.name);

        const storageKey = `agent:${agentId}:lastSessionId`;
        let existingSessionId: number | null = null;
        try {
          const raw = typeof window !== "undefined" ? window.localStorage.getItem(storageKey) : null;
          existingSessionId = raw ? Number(raw) : null;
          if (Number.isNaN(existingSessionId || undefined)) existingSessionId = null;
        } catch (_) {
          existingSessionId = null;
        }

        let activeSessionId: number | null = null;

        // Пытаемся загрузить историю существующей сессии
        if (existingSessionId) {
          try {
            const history = await apiFetch(`/sessions/${existingSessionId}/history`);
            if (history?.id) {
              activeSessionId = history.id;
              setSessionId(history.id);
              if (history?.messages) {
                const msgs: Message[] = history.messages.map((m: any) => ({
                  sender: m.sender === "user" ? "user" : "agent",
                  text: m.text,
                }));
                setMessages(msgs);
              }
            }
          } catch (_) {
            // Если история не загрузилась (например, 404), создаём новую сессию
            activeSessionId = null;
          }
        }

        // Если нет валидной сессии — создаём новую
        if (!activeSessionId) {
          const session = await apiFetch(`/sessions/`, {
            method: "POST",
            body: JSON.stringify({ agent_id: agentId }),
          });
          activeSessionId = session.id;
          setSessionId(session.id);

          // Загружаем историю (если вдруг созданная сессия уже имеет сообщения)
          try {
            const history = await apiFetch(`/sessions/${session.id}/history`);
            if (history?.messages) {
              const msgs: Message[] = history.messages.map((m: any) => ({
                sender: m.sender === "user" ? "user" : "agent",
                text: m.text,
              }));
              setMessages(msgs);
            }
          } catch (_) {
            // игнорируем ошибки истории для только что созданной сессии
          }

          // Сохраняем id сессии в localStorage для последующих открытий
          try {
            if (typeof window !== "undefined") {
              window.localStorage.setItem(storageKey, String(session.id));
            }
          } catch (_) {
            // игнорируем ошибки записи в localStorage
          }
        }
      } catch (err) {
        console.error("Ошибка инициализации чата:", err);
      }
    }
    if (agentId) initChat();
  }, [agentId]);

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;

    const userMessage: Message = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await apiFetch(`/sessions/${sessionId}/message`, {
        method: "POST",
        body: JSON.stringify({ text: userMessage.text }),
      });

      const reply: Message = { sender: "agent", text: response.reply };
      setMessages((msgs) => [...msgs, reply]);

      // Убедимся, что текущая сессия сохранена как последняя для этого агента
      try {
        if (typeof window !== "undefined") {
          window.localStorage.setItem(`agent:${agentId}:lastSessionId`, String(sessionId));
        }
      } catch (_) {
        // игнорируем ошибки записи в localStorage
      }
    } catch (err) {
      console.error("Ошибка при отправке сообщения:", err);
      setMessages((msgs) => [
        ...msgs,
        { sender: "agent", text: "Ошибка сервера" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="bg-blue-600 text-white p-4 font-bold text-lg flex justify-between items-center">
        <span>Чат с агентом: {agentName || "..."}</span>
        <div className="flex items-center gap-2 ml-auto">
          <Link
            href={`/agents/${agentId}`}
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
          >
            Редактировать
          </Link>
          <Link
            href="/"
            className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300"
          >
            К списку агентов
          </Link>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-lg max-w-[70%] ${
              msg.sender === "user"
                ? "bg-green-500 text-white ml-auto"
                : "bg-white text-gray-900 border"
            }`}
          >
            {msg.text}
          </div>
        ))}
        {loading && (
          <div className="text-gray-500 italic">Агент печатает...</div>
        )}
      </div>

      <div className="p-4 bg-white border-t flex gap-2">
        <input
          type="text"
          placeholder="Введите сообщение..."
          className="flex-1 border rounded p-2 text-gray-900"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          onClick={sendMessage}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
          disabled={loading || !sessionId}
        >
          Отправить
        </button>
      </div>
    </div>
  );
}