"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL}/auth/login`;
      const body = new URLSearchParams({ username: email, password });

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(txt || "Login failed");
      }

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Ошибка входа");
    }
  }

  return (
    <div className="flex justify-center items-center h-screen bg-gray-100">
      <form onSubmit={handleLogin} className="bg-white p-6 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4 text-gray-900">Вход</h1>
        {error && <div className="text-red-600 mb-2 whitespace-pre-wrap">{error}</div>}
        <input
          type="email"
          placeholder="Email"
          className="w-full p-2 border rounded mb-2 text-gray-900 placeholder-gray-500"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="username"
        />
        <input
          type="password"
          placeholder="Пароль"
          className="w-full p-2 border rounded mb-4 text-gray-900 placeholder-gray-500"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
        <button
          type="submit"
          className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
        >
          Войти
        </button>
        <p className="mt-4 text-sm text-center text-gray-800">
          Нет аккаунта?{" "}
          <button
            type="button"
            className="text-green-600 hover:underline font-medium"
            onClick={() => router.push("/register")}
          >
            Зарегистрироваться
          </button>
        </p>
      </form>
    </div>
  );
}