"use client";

import { ReactNode, useEffect } from "react";
import Cookies from "js-cookie";
import { useAuthStore } from "@/store/auth";
import { getMe } from "@/lib/api";

export function RootProviders({ children }: { children: ReactNode }) {
  const { setAuth, clearAuth, loading, token, user } = useAuthStore();

  useEffect(() => {
    const init = async () => {
      const existing = Cookies.get("ai_deals_token");
      if (!existing) { clearAuth(); return; }
      try {
        const me = await getMe(existing);
        setAuth({ access_token: existing, token_type: "bearer", user: me });
      } catch {
        clearAuth();
      }
    };
    if (loading && !token && !user) init();
  }, [loading, token, user, setAuth, clearAuth]);

  return <>{children}</>;
}
