"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

interface KnowledgeUploadProps {
  agentId: number;
}

export const KnowledgeUpload = ({ agentId }: KnowledgeUploadProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    const allowed = [".txt", ".pdf", ".docx"];
    const ext = selected.name.slice(selected.name.lastIndexOf(".")).toLowerCase();
    if (!allowed.includes(ext)) {
      setStatus("Только файлы .txt, .pdf, .docx разрешены");
      return;
    }

    setFile(selected);
    setStatus(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setStatus("Сначала выберите файл");
      return;
    }

    setLoading(true);
    setStatus(null);

    const formData = new FormData();
    formData.append("agent_id", agentId.toString());
    formData.append("file", file);

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/knowledge/upload`, {
        method: "POST",
        body: formData,
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          // Content-Type не ставим, fetch сам выставит multipart/form-data
        },
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      const res = await response.json();
      setStatus(`Файл "${res.filename}" успешно загружен. ${res.chunks} чанков создано.`);
      setFile(null);
      router.push(`/agents/${agentId}`);
    } catch (err: any) {
      setStatus(`Ошибка: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border rounded shadow-md bg-white">
      <h3 className="text-lg font-semibold mb-2">Загрузка базы знаний</h3>
      <input
        type="file"
        id="knowledge-file"
        className="hidden"
        onChange={handleFileChange}
      />
      <label
        htmlFor="knowledge-file"
        className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded cursor-pointer hover:bg-gray-50"
      >
        {file ? file.name : "Перетащите файл сюда или кликните для выбора"}
      </label>

      <button
        className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        onClick={handleUpload}
        disabled={loading}
      >
        {loading ? "Загрузка..." : "Загрузить"}
      </button>

      {status && <p className="mt-2 text-sm text-gray-700">{status}</p>}
    </div>
  );
};
