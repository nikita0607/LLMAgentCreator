"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
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
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}