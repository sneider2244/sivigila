"use client";

import { useCallback } from "react";
import { useUserStore } from "@/store/useUserStore";
import { login as loginRequest } from "@/lib/auth";
import type { Usuario } from "@/types";

export function useAuth() {
  const user = useUserStore((state) => state.user);
  const accessToken = useUserStore((state) => state.accessToken);
  const setSession = useUserStore((state) => state.setSession);
  const clearSession = useUserStore((state) => state.clearSession);

  const login = useCallback(
    async (username: string, password: string): Promise<Usuario> => {
      const response = await loginRequest(username, password);
      setSession({
        user: response.user,
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      });
      return response.user;
    },
    [setSession],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  return {
    user,
    accessToken,
    isAuthenticated: Boolean(user && accessToken),
    login,
    logout,
  };
}
