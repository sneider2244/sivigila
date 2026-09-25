export type Rol =
  | "UPGD"
  | "UI"
  | "MUNICIPAL"
  | "DEPARTAMENTAL"
  | "NACIONAL"
  | "DOCENTE";

export interface User {
  id: string;
  nombre: string;
  email: string;
  rol: Rol;
  codUpgd?: string;
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
