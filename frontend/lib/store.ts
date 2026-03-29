import { create } from 'zustand';
import { User } from './types';
import { authAPI } from './api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string, referralCode?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
  updateCredits: (credits: number) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email: string, password: string) => {
    const response = await authAPI.login(email, password);
    const { access_token } = response.data;
    localStorage.setItem('token', access_token);
    
    const userResponse = await authAPI.getMe();
    set({ user: userResponse.data, isAuthenticated: true });
  },

  register: async (email: string, password: string, fullName?: string, referralCode?: string) => {
    await authAPI.register({ email, password, full_name: fullName, referral_code: referralCode });
    await useAuthStore.getState().login(email, password);
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }
    try {
      const response = await authAPI.getMe();
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem('token');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  updateCredits: (credits: number) => {
    set((state) => ({
      user: state.user ? { ...state.user, credits } : null,
    }));
  },
}));
