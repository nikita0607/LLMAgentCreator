"use client";

import { useEffect, useRef, useState } from "react";
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [agentName, setAgentName] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [useLastSession, setUseLastSession] = useState(true); // Flag to track if we're using last session

  // Scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Function to create a new session
  const createNewSession = async () => {
    try {
      const sessionResponse = await apiFetch(`/sessions/`, {
        method: "POST",
        body: JSON.stringify({ agent_id: agentId }),
      });
      
      // Check if response has session_id (new format) or id (old format)
      const actualSessionId = sessionResponse.session_id || sessionResponse.id;
      setSessionId(actualSessionId);
      setUseLastSession(false); // We're now using a new session
      
      // Clear messages and add initial forced message if exists
      setMessages([]);
      
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
    } catch (err) {
      console.error("Ошибка создания новой сессии:", err);
    }
  };

  // Загружаем агента и используем последнюю сессию или создаём новую
  useEffect(() => {
    async function initChat() {
      try {
        const agent = await apiFetch(`/agents/${agentId}`);
        setAgentName(agent.name);

        // Try to get the last session first
        if (useLastSession) {
          try {
            const lastSession = await apiFetch(`/sessions/last/${agentId}`);
            const actualSessionId = lastSession.id;
            setSessionId(actualSessionId);
            setUseLastSession(true);
            
            // Load history for the last session
            try {
              const history = await apiFetch(`/sessions/${actualSessionId}/history`);
              if (history?.messages) {
                const msgs: Message[] = history.messages.map((m: any) => ({
                  sender: m.sender === "user" ? "user" : "agent",
                  text: m.text,
                }));
                setMessages(msgs);
              }
            } catch (historyErr) {
              console.log("No history available for last session:", historyErr);
              setMessages([]);
            }
            return; // Successfully loaded last session, exit early
          } catch (lastSessionErr) {
            console.log("No last session found, creating new one:", lastSessionErr);
            // Continue to create new session if no last session found
          }
        }
        
        // Create new session if no last session or if explicitly requested
        await createNewSession();
      } catch (err) {
        console.error("Ошибка инициализации чата:", err);
      }
    }
    if (agentId) initChat();
  }, [agentId, useLastSession]);

  const sendMessage = async () => {
    if (!input.trim() || !sessionId) return;

    const userMessage: Message = { sender: "user", text: input };
    setMessages((msgs: Message[]) => [...msgs, userMessage]);
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
        const agentMessages: Message[] = response.messages
          .filter((text: string) => text && text.trim() !== "") // Filter out empty/null messages
          .map((text: string) => ({
            sender: "agent" as const,
            text: text
          }));
        if (agentMessages.length > 0) { // Only add if there are non-empty messages
          setMessages((msgs: Message[]) => [...msgs, ...agentMessages]);
        }
      } else if (response.reply) {
        console.log("Received single reply:", response.reply);
        // Only add non-empty replies
        if (response.reply && response.reply.trim() !== "") {
          const reply: Message = { sender: "agent", text: response.reply };
          setMessages((msgs: Message[]) => [...msgs, reply]);
        }
      }
    } catch (err) {
      console.error("Ошибка при отправке сообщения:", err);
      setMessages((msgs: Message[]) => [
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
          <div className="flex items-center gap-2">
            <button
              onClick={createNewSession}
              className="bg-transparent border border-cyan-400 text-cyan-400 px-4 py-2 font-mono hover:bg-cyan-400 hover:text-black transition-all duration-200 flex items-center gap-2"
              style={{ borderRadius: '0.25rem' }}
            >
              <span>🔄</span>
              <span>new session</span>
            </button>
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
            <div ref={messagesEndRef} />
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