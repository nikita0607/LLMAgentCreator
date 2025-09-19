"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

export default function CreateAgentPage() {
  const [name, setName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [error, setError] = useState("");
  const [agentId, setAgentId] = useState<number | null>(null); // хранит ID созданного агента
  const [isCreating, setIsCreating] = useState(false);
  const router = useRouter();

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setIsCreating(true);
    setError("");
    
    try {
      const data = await apiFetch("/agents", {
        method: "POST",
        body: JSON.stringify({ name, system_prompt: systemPrompt, voice_id: voiceId }),
      });

      setAgentId(data.id); // сохраняем ID созданного агента
      
      // Перенаправляем на страницу редактирования созданного агента
      router.push(`/agents/${data.id}`);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Ошибка создания агента";
      setError(errorMessage);
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="flex flex-col justify-center items-center p-6 bg-gray-700 min-h-screen space-y-6">
      {!agentId && (
        <form 
          onSubmit={handleCreate} 
          className="bg-gray-600 border border-green-400 p-6 w-full max-w-lg space-y-4 font-mono" 
          style={{ 
            borderRadius: '0.25rem',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)'
          }}
        >
          <div className="flex items-center gap-2 mb-4">
            <span className="text-green-400">$</span>
            <h1 className="text-2xl font-bold text-green-400">touch new_agent.py</h1>
          </div>
          {error && (
            <div className="text-red-400 bg-gray-900 p-2 border border-red-500" style={{ borderRadius: '0.25rem' }}>
              ERROR: {error}
            </div>
          )}

          <label className="block text-green-400">agent.name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-2 bg-gray-900 border border-gray-600 text-green-400 font-mono focus:border-green-400 focus:outline-none"
            style={{ borderRadius: '0.25rem' }}
            placeholder="enter agent name..."
          />

          <label className="block text-green-400">agent.system_prompt</label>
          <textarea
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            className="w-full p-2 bg-gray-900 border border-gray-600 text-green-400 font-mono focus:border-green-400 focus:outline-none"
            style={{ borderRadius: '0.25rem' }}
            placeholder="# System instructions for the agent..."
            rows={4}
          />

          <label className="block text-green-400">agent.voice_id</label>
          <input
            type="text"
            value={voiceId}
            onChange={(e) => setVoiceId(e.target.value)}
            className="w-full p-2 bg-gray-900 border border-gray-600 text-green-400 font-mono focus:border-green-400 focus:outline-none"
            style={{ borderRadius: '0.25rem' }}
            placeholder="default_voice"
          />

          <button
            type="submit"
            disabled={isCreating}
            className="w-full bg-green-500 text-black py-2 font-mono hover:bg-green-400 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors duration-200"
            style={{ borderRadius: '0.25rem' }}
          >
            {isCreating ? "python create_agent.py --running..." : "python create_agent.py --execute"}
          </button>
        </form>
      )}
    </div>
  );
}
