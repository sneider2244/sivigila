import axios from "axios";
import { api } from "@/lib/axios";
import {
  mapFichaDatosBasicosOut,
  mapFichaDatosBasicosToRaw,
  mapFichaDatosComplementarios,
  mapFichaDatosComplementariosOut,
  mapFichaDatosComplementariosToRaw,
  type FichaDatosBasicos,
  type FichaDatosBasicosOut,
  type FichaDatosBasicosOutRaw,
  type FichaDatosComplementarios,
  type FichaDatosComplementariosOut,
  type FichaDatosComplementariosOutRaw,
  type FichaDatosComplementariosRaw,
} from "@/types";

export async function createFichaDatosBasicos(
  ficha: FichaDatosBasicos,
): Promise<FichaDatosBasicosOut> {
  const { data } = await api.post<FichaDatosBasicosOutRaw>(
    "/fichas/datos-basicos",
    mapFichaDatosBasicosToRaw(ficha),
  );
  return mapFichaDatosBasicosOut(data);
}

export async function createFichaDatosComplementarios(
  ficha: FichaDatosComplementarios,
): Promise<FichaDatosComplementarios> {
  const { data } = await api.post<FichaDatosComplementariosRaw>(
    "/fichas/datos-complementarios",
    mapFichaDatosComplementariosToRaw(ficha),
  );
  return mapFichaDatosComplementarios(data);
}

export async function getFichaDatosComplementarios(
  fichaBasicaId: number,
): Promise<FichaDatosComplementariosOut | null> {
  try {
    const { data } = await api.get<FichaDatosComplementariosOutRaw>(
      `/fichas/datos-complementarios/${fichaBasicaId}`,
    );
    return mapFichaDatosComplementariosOut(data);
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) {
      return null;
    }
    throw err;
  }
}
