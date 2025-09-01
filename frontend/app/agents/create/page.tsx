"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { KnowledgeUpload } from "@/components/KnowledgeUpload";

export default function CreateAgentPage() {
  const [name, setName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [error, setError] = useState("");
  const [agentId, setAgentId] = useState<number | null>(null); // хранит ID созданного агента
  const router = useRouter();

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const data = await apiFetch("/agents", {
        method: "POST",
        body: JSON.stringify({ name, system_prompt: systemPrompt, voice_id: voiceId }),
      });

      setAgentId(data.id); // сохраняем ID созданного агента
      setError("");
    } catch (err: any) {
      setError(err.message || "Ошибка создания агента");
    }
  }

  return (
    <div className="flex flex-col justify-center items-center p-6 bg-gray-100 min-h-screen space-y-6">
      {!agentId ? (
        <form onSubmit={handleCreate} className="bg-white p-6 rounded shadow-md w-full max-w-lg space-y-4">
          <h1 className="text-2xl font-bold mb-4 text-gray-900">Создать агента</h1>
          {error && <div className="text-red-600">{error}</div>}

          <label className="block text-gray-800">Имя агента</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-2 border rounded text-gray-900 placeholder-gray-500"
            placeholder="Имя агента"
          />

          <label className="block text-gray-800">Системный промпт</label>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            className="w-full p-2 border rounded text-gray-900 placeholder-gray-500"
            placeholder="Например: Ты помощник, который отвечает вежливо"
          />

          <label className="block text-gray-800">Выбор голоса</label>
          <input
            type="text"
            value={voiceId}
            onChange={(e) => setVoiceId(e.target.value)}
            className="w-full p-2 border rounded text-gray-900 placeholder-gray-500"
            placeholder="voice_id (например default_voice)"
          />

          <button
            type="submit"
            className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600"
          >
            Создать
          </button>
        </form>
      ) : (
        <div className="w-full max-w-lg">
          <h2 className="text-xl font-semibold mb-4">Загрузка базы знаний для агента</h2>
          <KnowledgeUpload agentId={agentId} />
        </div>
      )}
    </div>
  );
}
