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

  if (loading) return <div className="p-4">Загрузка...</div>;

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold text-gray-400">Мои агенты</h1>
        <Link
          href="/agents/create"
          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          Создать агента
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agents.map((agent) => (
          <div key={agent.id} className="border p-4 rounded shadow bg-white">
            <h2 className="text-lg font-semibold text-gray-900">{agent.name}</h2>
            <p className="text-gray-700">{agent.description}</p>
            <div className="mt-2 flex gap-2">
              <Link
                href={`/agents/${agent.id}`}
                className="text-blue-500 hover:underline"
              >
                Редактировать
              </Link>
              <Link
                href={`/agents/${agent.id}/chat`}
                className="text-green-500 hover:underline"
              >
                Открыть чат
              </Link>
              <button
                onClick={() => setShowDeleteDialog(agent.id)}
                className="text-red-500 hover:underline"
                disabled={deletingAgent === agent.id}
              >
                {deletingAgent === agent.id ? "Удаление..." : "Удалить"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Диалог подтверждения удаления */}
      {showDeleteDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Подтверждение удаления
            </h3>
            <p className="text-gray-700 mb-6">
              Вы уверены, что хотите удалить агента "{agents.find((a: Agent) => a.id === showDeleteDialog)?.name}"? 
              Это действие нельзя отменить.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteDialog(null)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
                disabled={deletingAgent === showDeleteDialog}
              >
                Отмена
              </button>
              <button
                onClick={() => handleDeleteAgent(showDeleteDialog)}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
                disabled={deletingAgent === showDeleteDialog}
              >
                {deletingAgent === showDeleteDialog ? "Удаление..." : "Удалить"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}