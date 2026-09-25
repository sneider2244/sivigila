"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getEscenarios } from "@/lib/docente";
import { useUserStore } from "@/store/useUserStore";
import type { EscenarioClinico } from "@/types";
import styles from "./escenarios.module.scss";

function EscenarioCard({ escenario }: { escenario: EscenarioClinico }) {
  return (
    <Link
      href={`/docente/escenarios/${escenario.id}`}
      className={styles.card}
    >
      <div className={styles.cardHeader}>
        <h3 className={styles.cardTitle}>{escenario.titulo}</h3>
        <span
          className={
            escenario.activo ? styles.badgeActive : styles.badgeInactive
          }
        >
          {escenario.activo ? "Activo" : "Inactivo"}
        </span>
      </div>
      <p className={styles.cardDesc}>{escenario.descripcion}</p>
      <p className={styles.cardMeta}>
        Evento: <strong>{escenario.codEvento}</strong>
      </p>
    </Link>
  );
}

export default function DocenteEscenariosPage() {
  const user = useUserStore((state) => state.user);
  const isDocente = user?.rol === "DOCENTE";

  const {
    data: escenarios = [],
    isLoading: escenariosLoading,
    isError: escenariosError,
  } = useQuery({
    queryKey: ["docente", "escenarios"],
    queryFn: getEscenarios,
    enabled: isDocente,
  });

  if (!isDocente) {
    return (
      <div className={styles.page}>
        <div className={styles.accessDenied}>Acceso solo para docentes</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Escenarios clínicos</h1>
        <p className={styles.subtitle}>
          Creá escenarios, asignalos a estudiantes y revisá sus fichas.
        </p>
      </header>

      <div className={styles.actions}>
        <Link href="/docente/escenarios/nuevo" className={styles.button}>
          Crear escenario
        </Link>
      </div>

      <section className={styles.section}>
        {escenariosLoading && (
          <p className={styles.banner}>Cargando escenarios…</p>
        )}
        {escenariosError && (
          <p className={styles.errorBanner}>
            No se pudieron cargar los escenarios.
          </p>
        )}
        {!escenariosLoading && !escenariosError && escenarios.length === 0 && (
          <p className={styles.banner}>No hay escenarios creados todavía.</p>
        )}
        {!escenariosLoading && !escenariosError && (
          <div className={styles.list}>
            {escenarios.map((escenario) => (
              <EscenarioCard key={escenario.id} escenario={escenario} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
