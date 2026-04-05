"use client";

import { create } from "zustand";
import Cookies from "js-cookie";
import type { User, TokenResponse } from "@/lib/api";

type AuthState = {
  user: User | null;
  token: string | null;
  loading: boolean;
  setAuth: (data: TokenResponse) => void;
  clearAuth: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  loading: true,
  setAuth: (data) => {
    Cookies.set("ai_deals_token", data.access_token, { expires: 7 });
    set({ user: data.user, token: data.access_token, loading: false });
  },
  clearAuth: () => {
    Cookies.remove("ai_deals_token");
    set({ user: null, token: null, loading: false });
  },
}));
