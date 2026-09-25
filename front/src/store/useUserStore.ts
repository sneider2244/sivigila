"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Usuario } from "@/types";

interface Session {
  user: Usuario;
  accessToken: string;
  refreshToken: string;
}

interface UserState {
  user: Usuario | null;
  accessToken: string | null;
  refreshToken: string | null;
  setSession: (session: Session) => void;
  setTokens: (accessToken: string, refreshToken?: string) => void;
  clearSession: () => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      setSession: ({ user, accessToken, refreshToken }) =>
        set({ user, accessToken, refreshToken }),
      setTokens: (accessToken, refreshToken) =>
        set((state) => ({
          accessToken,
          refreshToken: refreshToken ?? state.refreshToken,
        })),
      clearSession: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    {
      name: "sivigila-user-session",
    },
  ),
);
