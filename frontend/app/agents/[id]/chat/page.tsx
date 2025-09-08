"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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

  // Загружаем агента и создаём сессию
  useEffect(() => {
    async function initChat() {
      try {
        const agent = await apiFetch(`/agents/${agentId}`);
        setAgentName(agent.name);

        const sessionResponse = await apiFetch(`/sessions/`, {
          method: "POST",
          body: JSON.stringify({ agent_id: agentId }),
        });
        
        // Check if response has session_id (new format) or id (old format)
        const actualSessionId = sessionResponse.session_id || sessionResponse.id;
        setSessionId(actualSessionId);
        
        // If there's an initial forced message, add it to messages
        if (sessionResponse.messages && sessionResponse.messages.length > 0) {
          const initialMessages: Message[] = sessionResponse.messages.map(text => ({
            sender: "agent" as const,
            text: text
          }));
          setMessages(initialMessages);
        } else if (sessionResponse.reply && sessionResponse.reply.trim()) {
          const initialMessage: Message = {
            sender: "agent",
            text: sessionResponse.reply
          };
          setMessages([initialMessage]);
        }

        // подгружаем историю, если есть
        if (actualSessionId) {
          try {
            const history = await apiFetch(`/sessions/${actualSessionId}/history`);
            if (history?.messages) {
              const msgs: Message[] = history.messages.map((m: any) => ({
                sender: m.sender === "user" ? "user" : "agent",
                text: m.text,
              }));
              // If we already have initial messages, append to them
              setMessages(prevMessages => {
                if (prevMessages.length > 0) {
                  // Merge with existing initial messages, avoiding duplicates
                  const existingTexts = new Set(prevMessages.map(m => m.text));
                  const newMsgs = msgs.filter(m => !existingTexts.has(m.text));
                  return [...prevMessages, ...newMsgs];
                } else {
                  return msgs;
                }
              });
            }
          } catch (historyErr) {
            console.log("No history available or error loading history:", historyErr);
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

      // Handle multiple messages from the response
      if (response.messages && response.messages.length > 0) {
        console.log("Received multiple messages:", response.messages);
        const agentMessages: Message[] = response.messages.map((text: string) => ({
          sender: "agent" as const,
          text: text
        }));
        setMessages((msgs) => [...msgs, ...agentMessages]);
      } else if (response.reply) {
        console.log("Received single reply:", response.reply);
        const reply: Message = { sender: "agent", text: response.reply };
        setMessages((msgs) => [...msgs, reply]);
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
      <div className="bg-blue-600 text-white p-4 font-bold text-lg">
        Чат с агентом: {agentName || "..."}
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