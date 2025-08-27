"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL}/auth/register`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      localStorage.setItem("token", data.access_token);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Ошибка регистрации");
    }
  }

  return (
    <div className="flex justify-center items-center h-screen bg-gray-100">
      <form onSubmit={handleRegister} className="bg-white p-6 rounded shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4 text-gray-900">Регистрация</h1>
        {error && <div className="text-red-600 mb-2 whitespace-pre-wrap">{error}</div>}
        <input
          type="email"
          placeholder="Email"
          className="w-full p-2 border rounded mb-2 text-gray-900 placeholder-gray-500"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="Пароль"
          className="w-full p-2 border rounded mb-4 text-gray-900 placeholder-gray-500"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button
          type="submit"
          className="w-full bg-green-500 text-white py-2 rounded hover:bg-green-600"
        >
          Зарегистрироваться
        </button>
        <p className="mt-4 text-sm text-center text-gray-800">
          Уже есть аккаунт?{" "}
          <button
            type="button"
            className="text-blue-600 hover:underline font-medium"
            onClick={() => router.push("/login")}
          >
            Войти
          </button>
        </p>
      </form>
    </div>
  );
}