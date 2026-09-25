import { api } from "@/lib/axios";
import {
  mapEscenarioAsignacion,
  mapEscenarioClinico,
  mapEstudianteDocente,
  mapFichaDatosBasicosOut,
  type EscenarioAsignacion,
  type EscenarioAsignacionRaw,
  type EscenarioClinico,
  type EscenarioClinicoRaw,
  type EstudianteDocente,
  type EstudianteDocenteRaw,
  type EvaluacionResult,
  type FichaDatosBasicosOut,
  type FichaDatosBasicosOutRaw,
} from "@/types";

export interface CrearEscenarioInput {
  titulo: string;
  descripcion: string;
  codEvento: string;
  datosEsperados: unknown;
  activo: boolean;
}

export async function getEscenarios(): Promise<EscenarioClinico[]> {
  const { data } = await api.get<EscenarioClinicoRaw[]>(
    "/docente/escenarios",
  );
  return data.map(mapEscenarioClinico);
}

export async function createEscenario(
  input: CrearEscenarioInput,
): Promise<EscenarioClinico> {
  const { data } = await api.post<EscenarioClinicoRaw>("/docente/escenarios", {
    titulo: input.titulo,
    descripcion: input.descripcion,
    cod_evento: input.codEvento,
    datos_esperados: input.datosEsperados,
    activo: input.activo,
  });
  return mapEscenarioClinico(data);
}

export async function asignarEscenario(
  escenarioId: number,
  estudianteIds: number[],
): Promise<EscenarioAsignacion[]> {
  const { data } = await api.post<EscenarioAsignacionRaw[]>(
    `/docente/escenarios/${escenarioId}/asignar`,
    { estudiante_ids: estudianteIds },
  );
  return data.map(mapEscenarioAsignacion);
}

export async function getEstudiantes(
  q?: string,
): Promise<EstudianteDocente[]> {
  const { data } = await api.get<EstudianteDocenteRaw[]>(
    "/docente/estudiantes",
    { params: q ? { q } : undefined },
  );
  return data.map(mapEstudianteDocente);
}

export async function getFichaBasica(
  id: number,
): Promise<FichaDatosBasicosOut> {
  const { data } = await api.get<FichaDatosBasicosOutRaw>(
    `/fichas/datos-basicos/${id}`,
  );
  return mapFichaDatosBasicosOut(data);
}

export async function getAsignaciones(): Promise<EscenarioAsignacion[]> {
  const { data } = await api.get<EscenarioAsignacionRaw[]>(
    "/docente/asignaciones",
  );
  return data.map(mapEscenarioAsignacion);
}

export async function evaluarFicha(
  fichaBasicaId: number,
  escenarioId: number,
): Promise<EvaluacionResult> {
  const { data } = await api.post<EvaluacionResult>("/docente/evaluar", {
    ficha_basica_id: fichaBasicaId,
    escenario_id: escenarioId,
  });
  return data;
}
