import { api } from "@/lib/axios";
import type { CatalogoEvento } from "@/types";

export async function getEventos(): Promise<CatalogoEvento[]> {
  const { data } = await api.get<CatalogoEvento[]>("/catalogos/eventos");
  return data;
}
