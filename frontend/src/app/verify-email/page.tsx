"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { verifyEmail } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import Link from "next/link";

function VerifyEmailInner() {
  const search = useSearchParams();
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Verifying your email...");

  useEffect(() => {
    const token = search.get("token");
    if (!token) {
      setStatus("error");
      setMessage("Missing verification token. Check your email link.");
      return;
    }
    const run = async () => {
      try {
        const data = await verifyEmail(token);
        setAuth(data);
        setStatus("success");
        setMessage("Email verified! Your free credits are now active.");
        setTimeout(() => router.push("/dashboard"), 2000);
      } catch (err: unknown) {
        setStatus("error");
        setMessage((err as Error).message || "Verification failed. Token may be expired.");
      }
    };
    run();
  }, [search, setAuth, router]);

  return (
    <div className="max-w-md mx-auto px-4 py-14">
      <h1 className="text-2xl font-bold mb-6">Email verification</h1>
      <div
        className={
          "border rounded-xl p-5 text-sm " +
          (status === "success"
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
            : status === "error"
            ? "border-red-500/30 bg-red-500/10 text-red-300"
            : "border-slate-700 bg-slate-900/40 text-slate-300")
        }
      >
        {status === "loading" && (
          <span className="animate-pulse">{message}</span>
        )}
        {status !== "loading" && (
          <>
            <p>{message}</p>
            {status === "success" && (
              <p className="text-xs text-slate-400 mt-2">
                Redirecting to dashboard...
              </p>
            )}
            {status === "error" && (
              <div className="mt-3">
                <Link
                  href="/register"
                  className="text-emerald-400 underline hover:text-emerald-300"
                >
                  Try registering again →
                </Link>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailInner />
    </Suspense>
  );
}
