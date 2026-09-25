"use client";

import { create } from "zustand";
import type { Caso, UPGD } from "@/types";

interface CasoState {
  upgdSeleccionada: UPGD | null;
  borrador: Partial<Caso> | null;
  setUpgd: (upgd: UPGD | null) => void;
  setBorrador: (borrador: Partial<Caso> | null) => void;
}

export const useCasoStore = create<CasoState>((set) => ({
  upgdSeleccionada: null,
  borrador: null,
  setUpgd: (upgd) => set({ upgdSeleccionada: upgd }),
  setBorrador: (borrador) => set({ borrador }),
}));
