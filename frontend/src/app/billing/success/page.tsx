"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";
import { getMe } from "@/lib/api";

export default function BillingSuccessPage() {
  const { token, setAuth } = useAuthStore();

  useEffect(() => {
    if (!token) return;
    const refresh = async () => {
      try {
        const me = await getMe(token);
        setAuth({ access_token: token, token_type: "bearer", user: me });
      } catch {}
    };
    const t = setTimeout(refresh, 2000);
    return () => clearTimeout(t);
  }, [token, setAuth]);

  return (
    <div className="max-w-md mx-auto px-4 py-16 text-center">
      <div className="text-5xl mb-6">🎉</div>
      <h1 className="text-2xl font-bold mb-3">Payment successful!</h1>
      <p className="text-slate-300 text-sm mb-2">
        Your subscription is now active. Credits have been added to your account.
      </p>
      <p className="text-slate-400 text-xs mb-8">
        It may take a few seconds for the credits to appear on your dashboard.
      </p>
      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          href="/dashboard"
          className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-semibold px-6 py-2.5 rounded"
        >
          Go to Dashboard →
        </Link>
        <Link
          href="/global-deals"
          className="border border-slate-700 hover:border-slate-500 text-slate-200 px-6 py-2.5 rounded"
        >
          Search Global Deals
        </Link>
      </div>
    </div>
  );
}
