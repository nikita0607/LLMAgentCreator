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
    <div className="flex justify-center items-center h-screen bg-black">
      <form 
        onSubmit={handleRegister} 
        className="bg-gray-800 border border-green-400 p-6 w-96 font-mono"
        style={{ 
          borderRadius: '0.25rem',
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)'
        }}
      >
        <div className="flex items-center gap-2 mb-4">
          <span className="text-green-400">$</span>
          <h1 className="text-2xl font-bold text-green-400">useradd --create</h1>
        </div>
        {error && (
          <div className="text-red-400 bg-gray-900 p-2 border border-red-500 mb-2" style={{ borderRadius: '0.25rem' }}>
            CREATE_ERROR: {error}
          </div>
        )}
        <input
          type="email"
          placeholder="new_user@domain.com"
          className="w-full p-2 bg-gray-900 border border-gray-600 text-green-400 font-mono mb-2 focus:border-green-400 focus:outline-none"
          style={{ borderRadius: '0.25rem' }}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="password"
          placeholder="••••••••"
          className="w-full p-2 bg-gray-900 border border-gray-600 text-green-400 font-mono mb-4 focus:border-green-400 focus:outline-none"
          style={{ borderRadius: '0.25rem' }}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button
          type="submit"
          className="w-full bg-green-500 text-black py-2 font-mono hover:bg-green-400 transition-colors duration-200"
          style={{ borderRadius: '0.25rem' }}
        >
          execute create_user.sh
        </button>
        <p className="mt-4 text-sm text-center text-gray-400">
          Already have account?{" "}
          <button
            type="button"
            className="text-blue-400 hover:text-blue-300 hover:underline font-medium"
            onClick={() => router.push("/login")}
          >
            ./login
          </button>
        </p>
      </form>
    </div>
  );
}