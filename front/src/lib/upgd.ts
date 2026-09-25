import { api } from "@/lib/axios";
import {
  mapUpgdCaracterizacion,
  mapUpgdCaracterizacionToRaw,
  type UpgdCaracterizacion,
  type UpgdCaracterizacionRaw,
} from "@/types";

export async function getUpgd(
  codPrestador: string,
): Promise<UpgdCaracterizacion> {
  const { data } = await api.get<UpgdCaracterizacionRaw>(
    `/upgd/${codPrestador}`,
  );
  return mapUpgdCaracterizacion(data);
}

export async function createUpgd(
  upgd: UpgdCaracterizacion,
): Promise<UpgdCaracterizacion> {
  const { data } = await api.post<UpgdCaracterizacionRaw>(
    "/upgd",
    mapUpgdCaracterizacionToRaw(upgd),
  );
  return mapUpgdCaracterizacion(data);
}

export async function updateUpgd(
  codPrestador: string,
  upgd: UpgdCaracterizacion,
): Promise<UpgdCaracterizacion> {
  const { data } = await api.put<UpgdCaracterizacionRaw>(
    `/upgd/${codPrestador}`,
    mapUpgdCaracterizacionToRaw(upgd),
  );
  return mapUpgdCaracterizacion(data);
}
