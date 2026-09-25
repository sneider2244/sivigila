import { api } from "@/lib/axios";
import {
  mapFichaDatosBasicos,
  mapFichaDatosBasicosToRaw,
  mapFichaDatosComplementarios,
  mapFichaDatosComplementariosToRaw,
  type FichaDatosBasicos,
  type FichaDatosBasicosRaw,
  type FichaDatosComplementarios,
  type FichaDatosComplementariosRaw,
} from "@/types";

export async function createFichaDatosBasicos(
  ficha: FichaDatosBasicos,
): Promise<FichaDatosBasicos> {
  const { data } = await api.post<FichaDatosBasicosRaw>(
    "/fichas/datos-basicos",
    mapFichaDatosBasicosToRaw(ficha),
  );
  return mapFichaDatosBasicos(data);
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
