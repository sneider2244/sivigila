"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Input } from "@/components/ui/Input";
import { asignarEscenario, getEstudiantes } from "@/lib/docente";
import type { EscenarioClinico, EstudianteDocente } from "@/types";
import styles from "./EstudianteSelector.module.scss";

function EstudianteCheckbox({
  estudiante,
  checked,
  onToggle,
}: {
  estudiante: EstudianteDocente;
  checked: boolean;
  onToggle: () => void;
}) {
  const identificacion = estudiante.numeroIdentificacion ?? "—";
  return (
    <li className={styles.estudianteItem}>
      <label className={styles.estudianteLabel}>
        <input
          type="checkbox"
          checked={checked}
          onChange={onToggle}
          aria-label={`Seleccionar a ${estudiante.nombreCompleto}`}
        />
        <span className={styles.estudianteInfo}>
          <span className={styles.estudianteNombre}>
            {estudiante.nombreCompleto}
          </span>
          <span className={styles.estudianteMeta}>
            {estudiante.username} · CC {identificacion}
          </span>
        </span>
      </label>
    </li>
  );
}

export function EstudianteSelector({
  escenario,
}: {
  escenario: EscenarioClinico;
}) {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [seleccionados, setSeleccionados] = useState<Set<number>>(
    () => new Set(),
  );
  const [asignarError, setAsignarError] = useState<string | null>(null);
  const [asignarSuccess, setAsignarSuccess] = useState(false);

  const {
    data: estudiantes = [],
    isLoading: estudiantesLoading,
    isError: estudiantesError,
  } = useQuery({
    queryKey: ["docente", "estudiantes", q],
    queryFn: () => getEstudiantes(q),
  });

  const asignarMutation = useMutation({
    mutationFn: (estudianteIds: number[]) =>
      asignarEscenario(escenario.id, estudianteIds),
    onSuccess: () => {
      setSeleccionados(new Set());
      setAsignarError(null);
      setAsignarSuccess(true);
      queryClient.invalidateQueries({
        queryKey: ["docente", "escenarios", escenario.id, "asignaciones"],
      });
    },
    onError: (err) => {
      setAsignarSuccess(false);
      setAsignarError(
        axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? "No se pudo asignar el escenario")
          : "No se pudo asignar el escenario",
      );
    },
  });

  const toggleSeleccion = (id: number) => {
    setSeleccionados((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleAsignar = () => {
    setAsignarError(null);
    setAsignarSuccess(false);
    const ids = Array.from(seleccionados);
    if (ids.length === 0) {
      setAsignarError("Seleccione al menos un estudiante");
      return;
    }
    asignarMutation.mutate(ids);
  };

  return (
    <div className={styles.selector}>
      <div className={styles.selectorSearch}>
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar por nombre, correo o identificación"
          aria-label={`Buscar estudiantes para ${escenario.titulo}`}
        />
      </div>

      {estudiantesLoading && (
        <p className={styles.banner}>Buscando estudiantes…</p>
      )}
      {estudiantesError && (
        <p className={styles.errorBanner}>No se pudieron cargar los estudiantes.</p>
      )}
      {!estudiantesLoading && !estudiantesError && estudiantes.length === 0 && (
        <p className={styles.banner}>No se encontraron estudiantes.</p>
      )}

      {estudiantes.length > 0 && (
        <ul className={styles.estudianteList}>
          {estudiantes.map((estudiante) => (
            <EstudianteCheckbox
              key={estudiante.id}
              estudiante={estudiante}
              checked={seleccionados.has(estudiante.id)}
              onToggle={() => toggleSeleccion(estudiante.id)}
            />
          ))}
        </ul>
      )}

      <div className={styles.selectorActions}>
        <button
          type="button"
          className={styles.button}
          onClick={handleAsignar}
          disabled={asignarMutation.isPending || seleccionados.size === 0}
        >
          {asignarMutation.isPending
            ? "Asignando…"
            : `Asignar seleccionados (${seleccionados.size})`}
        </button>
      </div>

      {asignarError && <p className={styles.errorBanner}>{asignarError}</p>}
      {asignarSuccess && (
        <p className={styles.successBanner}>
          Estudiantes asignados correctamente.
        </p>
      )}
    </div>
  );
}
