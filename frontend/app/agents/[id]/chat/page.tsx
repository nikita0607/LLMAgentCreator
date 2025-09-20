"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

interface Message {
  sender: "user" | "agent";
  text: string;
}

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
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
          const initialMessages: Message[] = sessionResponse.messages.map((text: string) => ({
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
    <div className="flex flex-col h-screen bg-gray-700">
      <div className="bg-gray-800 border-b border-green-400 text-green-400 p-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-2 text-green-400 hover:text-green-300 transition-colors font-mono"
            >
              <span className="text-xl">←</span>
              <span>cd ..</span>
            </button>
            <div className="flex items-center gap-2">
              <span className="text-green-400 font-mono">$</span>
              <h1 className="font-bold text-lg font-mono">
                ./chat --agent="{agentName || "loading..."}" --session={sessionId}
              </h1>
            </div>
          </div>
          <Link
            href={`/agents/${agentId}`}
            className="bg-transparent border border-cyan-400 text-cyan-400 px-4 py-2 font-mono hover:bg-cyan-400 hover:text-black transition-all duration-200 flex items-center gap-2"
            style={{ borderRadius: '0.25rem' }}
          >
            <span>⚙️</span>
            <span>vim config</span>
          </Link>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-gray-900">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="space-y-6">
            {messages.map((msg, idx) => (
              <div key={idx} className="w-full">
                <div className={`flex ${
                  msg.sender === "user" ? "justify-end" : "justify-start"
                }`}>
                  <div
                    className={`p-4 font-mono ${
                      msg.sender === "user"
                        ? "bg-gray-800 border border-green-400 max-w-2xl"
                        : "bg-gray-900 border border-gray-600 hover:border-green-400 transition-colors duration-200 w-full"
                    }`}
                    style={{ borderRadius: '0.25rem' }}
                  >
                    <div className="text-xs opacity-70 mb-2">
                      {msg.sender === "user" ? "user@terminal:~$" : "agent@system:~$"}
                    </div>
                    <div className={msg.sender === "user" ? "text-green-400" : "text-gray-300"}>
                      {msg.text}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="w-full">
                <div className="bg-gray-900 border border-gray-600 p-4 font-mono" style={{ borderRadius: '0.25rem' }}>
                  <div className="text-xs opacity-70 mb-2">agent@system:~$</div>
                  <div className="text-cyan-400 flex items-center gap-2">
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                    <span>agent is typing...</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-gray-800 border-t border-green-400">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-2">
            <div className="flex-1 flex items-center">
              <span className="text-green-400 font-mono mr-2">$</span>
              <input
                type="text"
                placeholder="enter message..."
                className="flex-1 bg-gray-900 border border-gray-600 text-green-400 p-2 font-mono focus:border-green-400 focus:outline-none"
                style={{ borderRadius: '0.25rem' }}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              />
            </div>
            <button
              onClick={sendMessage}
              className="bg-green-500 text-black px-4 py-2 font-mono hover:bg-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
              style={{ borderRadius: '0.25rem' }}
              disabled={loading || !sessionId}
            >
              send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}