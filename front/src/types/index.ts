export type Rol =
  | "UPGD"
  | "UI"
  | "MUNICIPAL"
  | "DEPARTAMENTAL"
  | "NACIONAL"
  | "DOCENTE";

export interface Usuario {
  id: number;
  username: string;
  nombreCompleto: string;
  rol: Rol;
  codUpgd: string | null;
  activo: boolean;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  user: Usuario;
}

export interface UPGD {
  codigo: string;
  nombre: string;
  departamento: string;
  municipio: string;
}

export interface Caso {
  id: string;
  estado: "borrador" | "notificado";
}
