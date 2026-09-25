"use client";

import { useCallback } from "react";
import { useUserStore } from "@/store/useUserStore";
import {
  login as loginRequest,
  register as registerRequest,
  updateRol as updateRolRequest,
  type RegisterInput,
} from "@/lib/auth";
import type { Rol, Usuario } from "@/types";

export function useAuth() {
  const user = useUserStore((state) => state.user);
  const accessToken = useUserStore((state) => state.accessToken);
  const setSession = useUserStore((state) => state.setSession);
  const setUser = useUserStore((state) => state.setUser);
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

  const register = useCallback(
    async (input: RegisterInput): Promise<Usuario> => {
      const response = await registerRequest(input);
      setSession({
        user: response.user,
        accessToken: response.accessToken,
        refreshToken: response.refreshToken,
      });
      return response.user;
    },
    [setSession],
  );

  const changeRol = useCallback(
    async (rol: Rol): Promise<Usuario> => {
      const updated = await updateRolRequest(rol);
      setUser(updated);
      return updated;
    },
    [setUser],
  );

  const logout = useCallback(() => {
    clearSession();
  }, [clearSession]);

  return {
    user,
    accessToken,
    isAuthenticated: Boolean(user && accessToken),
    login,
    register,
    changeRol,
    logout,
  };
}
