"use client";

import { useEffect, useState } from "react";
import { apiFetch, deleteAgent } from "@/lib/api";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Agent {
  id: number;
  name: string;
  description: string;
}

export default function HomePage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingAgent, setDeletingAgent] = useState<number | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState<number | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    async function loadAgents() {
      try {
        const data = await apiFetch("/agents");
        setAgents(data);
      } catch (err) {
        console.error("Ошибка загрузки агентов:", err);
      } finally {
        setLoading(false);
      }
    }
    loadAgents();
  }, [router]);

  const handleDeleteAgent = async (agentId: number) => {
    try {
      setDeletingAgent(agentId);
      await deleteAgent(agentId);
      setAgents(agents.filter((agent: Agent) => agent.id !== agentId));
      setShowDeleteDialog(null);
    } catch (err) {
      console.error("Ошибка удаления агента:", err);
      alert("Ошибка при удалении агента");
    } finally {
      setDeletingAgent(null);
    }
  };

  if (loading) return <div className="p-4 text-green-400 font-mono">▶ Загрузка...</div>;

  return (
    <div className="p-6 min-h-screen bg-gray-900">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <span className="text-green-400 text-xl font-mono">$</span>
          <h1 className="text-2xl font-bold text-green-400 font-mono">ls ~/agents</h1>
        </div>
        <Link
          href="/agents/create"
          className="bg-transparent border border-green-400 text-green-400 px-4 py-2 font-mono hover:bg-green-400 hover:text-black transition-all duration-200 flex items-center gap-2"
          style={{ borderRadius: '0.25rem' }}
        >
          <span>+</span>
          <span>mkdir new_agent</span>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {agents.map((agent) => (
          <div 
            key={agent.id} 
            className="bg-gray-800 border border-gray-700 p-4 font-mono hover:border-green-400 transition-all duration-200 group"
            style={{ borderRadius: '0.25rem', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.3)' }}
            onClick={() => {location = "/agents/"+agent.id}}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-green-400">&gt;</span>
                <h2 className="text-lg font-semibold text-green-400">{agent.name}</h2>
              </div>
              <span className="text-gray-500 text-xs">agent.py</span>
            </div>
            <p className="text-gray-300 text-sm mb-4 pl-4 border-l-2 border-gray-600 group-hover:border-green-400 transition-colors duration-200">
              {agent.description}
            </p>
            <div className="flex gap-3 text-sm">
              <Link
                href={`/agents/${agent.id}`}
                className="text-blue-400 hover:text-blue-300 hover:underline flex items-center gap-1"
              >
                <span>⚙️</span>
                <span>edit</span>
              </Link>
              <Link
                href={`/agents/${agent.id}/chat`}
                className="text-green-400 hover:text-green-300 hover:underline flex items-center gap-1"
              >
                <span>💬</span>
                <span>chat</span>
              </Link>
              <button
                onClick={() => setShowDeleteDialog(agent.id)}
                className="text-red-400 hover:text-red-300 flex items-center gap-1 p-1"
                disabled={deletingAgent === agent.id}
              >
                <span>🗑️</span>
                <span>{deletingAgent === agent.id ? "removing..." : "rm"}</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Terminal-style Delete Confirmation Dialog */}
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div 
            className="bg-gray-800 border border-green-400 p-6 max-w-md w-full mx-4 font-mono"
            style={{ borderRadius: '0.25rem', boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="text-red-400">⚠️</span>
              <h3 className="text-lg font-semibold text-red-400">
                rm -rf confirmation
              </h3>
            </div>
            <div className="bg-gray-900 p-3 mb-4 border border-gray-600" style={{ borderRadius: '0.25rem' }}>
              <p className="text-gray-300 text-sm">
                $ rm -rf "{agents.find((a: Agent) => a.id === showDeleteDialog)?.name}"
              </p>
              <p className="text-yellow-400 text-xs mt-2">
                ⚠️ This action cannot be undone. Continue? [y/N]
              </p>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteDialog(null)}
                className="px-4 py-2 text-gray-400 border border-gray-600 font-mono hover:bg-gray-700 hover:border-gray-500 transition-colors duration-200"
                style={{ borderRadius: '0.25rem' }}
                disabled={deletingAgent === showDeleteDialog}
              >
                N (cancel)
              </button>
              <button
                onClick={() => handleDeleteAgent(showDeleteDialog)}
                className="px-4 py-2 bg-red-500 text-white border border-red-500 font-mono hover:bg-red-600 hover:border-red-600 disabled:opacity-50 transition-colors duration-200"
                style={{ borderRadius: '0.25rem' }}
                disabled={deletingAgent === showDeleteDialog}
              >
                {deletingAgent === showDeleteDialog ? "executing..." : "Y (confirm)"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}