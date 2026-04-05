"use client";

import { useState } from "react";
import { registerUser } from "@/lib/api";
import Link from "next/link";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMsg(null);
    setLoading(true);
    try {
      await registerUser(email, password, null);
      setMsg(
        "✅ Registration successful! Check your email to verify your account and activate your free credits."
      );
    } catch (err: unknown) {
      setError((err as Error).message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-14">
      <div className="mb-8">
        <h1 className="text-2xl font-bold mb-2">Create your account</h1>
        <p className="text-slate-400 text-sm">
          Verify your email and get{" "}
          <span className="text-emerald-400 font-semibold">3 free</span> property analyses.
        </p>
      </div>

      {msg ? (
        <div className="border border-emerald-500/30 bg-emerald-500/10 rounded-xl p-5 text-sm text-emerald-300">
          {msg}
          <div className="mt-3">
            <Link href="/login" className="text-emerald-400 underline hover:text-emerald-300">
              Go to login →
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={onSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium mb-1.5">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1.5">Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              className="w-full"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-60 text-slate-900 font-semibold py-2.5 rounded"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
          {error && (
            <p className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded px-3 py-2">
              {error}
            </p>
          )}
          <p className="text-xs text-slate-500 text-center">
            Already have an account?{" "}
            <Link href="/login" className="text-emerald-400 hover:text-emerald-300">
              Log in
            </Link>
          </p>
        </form>
      )}
    </div>
  );
}
