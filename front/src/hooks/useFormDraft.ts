"use client";

import { useCallback, useEffect, useRef } from "react";

export function useFormDraft<T>(
  key: string | null,
  values: T,
  restore: (v: T) => void,
) {
  const restoreRef = useRef(restore);
  const firstSaveRef = useRef(true);

  useEffect(() => {
    restoreRef.current = restore;
  });

  useEffect(() => {
    if (typeof window === "undefined" || !key) return;
    try {
      const raw = window.localStorage.getItem(key);
      if (raw != null) {
        restoreRef.current(JSON.parse(raw) as T);
      }
    } catch {
      // draft corrupto o no disponible; se ignora
    }
  }, [key]);

  useEffect(() => {
    if (typeof window === "undefined" || !key) return;
    if (firstSaveRef.current) {
      firstSaveRef.current = false;
      return;
    }
    const timer = setTimeout(() => {
      try {
        window.localStorage.setItem(key, JSON.stringify(values));
      } catch {
        // cuota excedida o almacenamiento no disponible; se ignora
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [key, values]);

  const clear = useCallback(() => {
    if (typeof window === "undefined" || !key) return;
    try {
      window.localStorage.removeItem(key);
    } catch {
      // se ignora
    }
  }, [key]);

  return { clear };
}
