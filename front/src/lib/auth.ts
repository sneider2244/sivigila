import { api } from "@/lib/axios";
import type { LoginResponse, Rol, Usuario } from "@/types";

interface UsuarioRaw {
  id: number;
  username: string;
  nombre_completo: string;
  numero_identificacion: string | null;
  rol: Rol;
  cod_upgd: string | null;
  activo: boolean;
}

interface LoginResponseRaw {
  access_token: string;
  refresh_token: string;
  token_type: string;
  usuario: UsuarioRaw;
}

export function mapUsuario(raw: UsuarioRaw): Usuario {
  return {
    id: raw.id,
    username: raw.username,
    nombreCompleto: raw.nombre_completo,
    numeroIdentificacion: raw.numero_identificacion,
    rol: raw.rol,
    codUpgd: raw.cod_upgd,
    activo: raw.activo,
  };
}

export function mapLoginResponse(raw: LoginResponseRaw): LoginResponse {
  return {
    accessToken: raw.access_token,
    refreshToken: raw.refresh_token,
    tokenType: raw.token_type,
    user: mapUsuario(raw.usuario),
  };
}

export async function login(
  username: string,
  password: string,
): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponseRaw>("/auth/login", {
    username,
    password,
  });
  return mapLoginResponse(data);
}

export interface RegisterInput {
  email: string;
  nombreCompleto: string;
  numeroIdentificacion: string;
  rol: Rol;
}

export async function register(
  input: RegisterInput,
): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponseRaw>("/auth/register", {
    email: input.email,
    nombre_completo: input.nombreCompleto,
    numero_identificacion: input.numeroIdentificacion,
    rol: input.rol,
  });
  return mapLoginResponse(data);
}

export async function updateRol(rol: Rol): Promise<Usuario> {
  const { data } = await api.patch<UsuarioRaw>("/auth/me", { rol });
  return mapUsuario(data);
}
