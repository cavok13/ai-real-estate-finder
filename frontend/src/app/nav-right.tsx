"use client";

import Link from "next/link";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";

export function ClientNavRight() {
  const { user, clearAuth } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    clearAuth();
    router.push("/");
  };

  if (!user) {
    return (
      <div className="flex items-center gap-3 text-sm">
        <Link href="/pricing" className="text-slate-400 hover:text-white transition-colors">
          Pricing
        </Link>
        <Link href="/login" className="text-slate-400 hover:text-white transition-colors">
          Login
        </Link>
        <Link
          href="/register"
          className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-3 py-1.5 rounded font-medium"
        >
          Get started
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-slate-400 hidden sm:inline truncate max-w-[160px]">
        {user.email}
      </span>
      <span className="text-emerald-400 font-semibold hidden sm:inline">
        {user.total_credits} cr
      </span>
      <Link href="/dashboard" className="text-slate-400 hover:text-white transition-colors">
        Dashboard
      </Link>
      <Link href="/global-deals" className="text-slate-400 hover:text-white transition-colors">
        Global Deals
      </Link>
      <Link href="/pricing" className="text-slate-400 hover:text-white transition-colors">
        Upgrade
      </Link>
      <button
        onClick={handleLogout}
        className="border border-slate-700 hover:border-slate-500 text-slate-300 px-3 py-1.5 rounded"
      >
        Logout
      </button>
    </div>
  );
}
