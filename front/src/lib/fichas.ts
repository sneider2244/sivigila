import { api } from "@/lib/axios";
import {
  mapFichaDatosBasicos,
  mapFichaDatosBasicosToRaw,
  type FichaDatosBasicos,
  type FichaDatosBasicosRaw,
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
