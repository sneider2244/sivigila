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

export type NivelComplejidad = 1 | 2 | 3 | 4;

export interface UpgdCaracterizacion {
  codPrestador: string;
  razonSocial: string;
  nit: string;
  nivelComplejidad: NivelComplejidad;
  cove: boolean;
  unidadAnalisis: boolean;
  internet: boolean;
  activo: boolean;
  departamentoCodigo: string | null;
  municipioCodigo: string | null;
}

export interface UpgdCaracterizacionRaw {
  cod_prestador: string;
  razon_social: string;
  nit: string;
  nivel_complejidad: number;
  cove: boolean;
  unidad_analisis: boolean;
  internet: boolean;
  activo: boolean;
  departamento_codigo: string | null;
  municipio_codigo: string | null;
}

export function mapUpgdCaracterizacion(
  raw: UpgdCaracterizacionRaw,
): UpgdCaracterizacion {
  return {
    codPrestador: raw.cod_prestador,
    razonSocial: raw.razon_social,
    nit: raw.nit,
    nivelComplejidad: raw.nivel_complejidad as NivelComplejidad,
    cove: raw.cove,
    unidadAnalisis: raw.unidad_analisis,
    internet: raw.internet,
    activo: raw.activo,
    departamentoCodigo: raw.departamento_codigo,
    municipioCodigo: raw.municipio_codigo,
  };
}

export function mapUpgdCaracterizacionToRaw(
  upgd: UpgdCaracterizacion,
): UpgdCaracterizacionRaw {
  return {
    cod_prestador: upgd.codPrestador,
    razon_social: upgd.razonSocial,
    nit: upgd.nit,
    nivel_complejidad: upgd.nivelComplejidad,
    cove: upgd.cove,
    unidad_analisis: upgd.unidadAnalisis,
    internet: upgd.internet,
    activo: upgd.activo,
    departamento_codigo: upgd.departamentoCodigo,
    municipio_codigo: upgd.municipioCodigo,
  };
}
