import { api } from "@/lib/axios";
import {
  mapEscenarioAsignacion,
  mapEscenarioClinico,
  type EscenarioAsignacion,
  type EscenarioAsignacionRaw,
  type EscenarioClinico,
  type EscenarioClinicoRaw,
  type EvaluacionResult,
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
  estudianteId: number,
): Promise<void> {
  await api.post(`/docente/escenarios/${escenarioId}/asignar`, {
    estudiante_id: estudianteId,
  });
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
