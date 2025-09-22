export async function apiFetch(path: string, options: RequestInit = {}) {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  // базовые заголовки
  const headers: HeadersInit = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  // если это НЕ FormData → ставим JSON
  if (!(options.body instanceof FormData)) {
    (headers as any)["Content-Type"] = "application/json";
  }

  // Use NEXT_PUBLIC_API_URL from environment or default to localhost
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const res = await fetch(`${apiUrl}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    throw new Error(await res.text());
  }

  return res.json();
}

export async function deleteAgent(agentId: number) {
  return apiFetch(`/agents/${agentId}`, {
    method: "DELETE",
  });
}