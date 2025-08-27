"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function ChatWindow({ sessionId }: { sessionId: number }) {
  const [messages, setMessages] = useState<{ sender: string; text: string }[]>([]);
  const [input, setInput] = useState("");

  async function sendMessage() {
    if (!input.trim()) return;

    setMessages([...messages, { sender: "user", text: input }]);

    const res = await apiFetch(`/sessions/${sessionId}/message`, {
      method: "POST",
      body: JSON.stringify({ text: input }),
    });

    setMessages((prev) => [...prev, { sender: "agent", text: res.reply }]);
    setInput("");
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 bg-gray-100">
        {messages.map((m, i) => (
          <div key={i} className={m.sender === "user" ? "text-right" : "text-left"}>
            <span className="inline-block px-3 py-2 my-1 rounded bg-white shadow">
              {m.text}
            </span>
          </div>
        ))}
      </div>
      <div className="p-2 flex gap-2 border-t">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 border rounded px-2"
          placeholder="Введите сообщение..."
        />
        <button onClick={sendMessage} className="bg-blue-500 text-white px-3 py-1 rounded">
          ➤
        </button>
      </div>
    </div>
  );
}