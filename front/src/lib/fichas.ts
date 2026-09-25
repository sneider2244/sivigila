import { api } from "@/lib/axios";
import {
  mapFichaDatosBasicosOut,
  mapFichaDatosBasicosToRaw,
  mapFichaDatosComplementarios,
  mapFichaDatosComplementariosToRaw,
  type FichaDatosBasicos,
  type FichaDatosBasicosOut,
  type FichaDatosBasicosOutRaw,
  type FichaDatosComplementarios,
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
