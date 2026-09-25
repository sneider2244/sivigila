import { api } from "@/lib/axios";
import {
  mapEstudianteAsignacion,
  type EstudianteAsignacion,
  type EstudianteAsignacionRaw,
} from "@/types";

export async function getMisEscenarios(): Promise<EstudianteAsignacion[]> {
  const { data } = await api.get<EstudianteAsignacionRaw[]>(
    "/estudiante/escenarios",
  );
  return data.map(mapEstudianteAsignacion);
}

export async function progresarEscenario(
  asignacionId: number,
  fichaBasicaId: number,
): Promise<void> {
  await api.post(`/estudiante/escenarios/${asignacionId}/progreso`, {
    ficha_basica_id: fichaBasicaId,
  });
}

export async function entregarEscenario(
  asignacionId: number,
  fichaBasicaId: number,
): Promise<void> {
  await api.post(`/estudiante/escenarios/${asignacionId}/entregar`, {
    ficha_basica_id: fichaBasicaId,
  });
}
