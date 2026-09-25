"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getMisEscenarios } from "@/lib/estudiante";
import type { EstudianteAsignacion } from "@/types";
import styles from "./mis-escenarios.module.scss";

const ESTADO_LABEL: Record<EstudianteAsignacion["estado"], string> = {
  ASIGNADO: "Asignado",
  EN_PROGRESO: "En progreso",
  COMPLETADO: "Completado",
};

const ESTADO_BADGE_CLASS: Record<EstudianteAsignacion["estado"], string> = {
  ASIGNADO: styles.badgeAsignado,
  EN_PROGRESO: styles.badgeEnProgreso,
  COMPLETADO: styles.badgeCompletado,
};

function AsignacionCard({ asignacion }: { asignacion: EstudianteAsignacion }) {
  const esEnProgreso =
    asignacion.estado === "EN_PROGRESO" && asignacion.fichaBasicaId != null;

  return (
    <article className={styles.card}>
      <div className={styles.cardHeader}>
        <h2 className={styles.cardTitle}>{asignacion.escenario.titulo}</h2>
        <span
          className={`${styles.badge} ${ESTADO_BADGE_CLASS[asignacion.estado]}`}
        >
          {ESTADO_LABEL[asignacion.estado]}
        </span>
      </div>
      <p className={styles.cardDesc}>{asignacion.escenario.descripcion}</p>
      <p className={styles.cardMeta}>
        Evento: <strong>{asignacion.escenario.codEvento}</strong>
      </p>
      <div className={styles.cardActions}>
        {asignacion.estado === "COMPLETADO" ? (
          <span className={styles.entregado}>Entregado</span>
        ) : esEnProgreso ? (
          <Link
            className={styles.button}
            href={{
              pathname: "/notificacion/datos-complementarios",
              query: {
                asignacion_id: String(asignacion.id),
                ficha_basica_id: String(asignacion.fichaBasicaId),
                cod_evento: asignacion.escenario.codEvento,
              },
            }}
          >
            Continuar
          </Link>
        ) : (
          <Link
            className={styles.button}
            href={{
              pathname: "/notificacion/datos-basicos",
              query: {
                asignacion_id: String(asignacion.id),
                cod_evento: asignacion.escenario.codEvento,
              },
            }}
          >
            Diligenciar
          </Link>
        )}
      </div>
    </article>
  );
}

export default function MisEscenariosPage() {
  const {
    data: asignaciones = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["estudiante", "escenarios"],
    queryFn: getMisEscenarios,
  });

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Mis escenarios</h1>
        <p className={styles.subtitle}>
          Escenarios clínicos asignados para diligenciar la ficha.
        </p>
      </header>

      {isLoading && <p className={styles.banner}>Cargando escenarios…</p>}
      {isError && (
        <p className={styles.errorBanner}>No se pudieron cargar los escenarios.</p>
      )}
      {!isLoading && !isError && asignaciones.length === 0 && (
        <p className={styles.empty}>Aún no tenés escenarios asignados.</p>
      )}
      {!isLoading && !isError && asignaciones.length > 0 && (
        <div className={styles.list}>
          {asignaciones.map((asignacion) => (
            <AsignacionCard key={asignacion.id} asignacion={asignacion} />
          ))}
        </div>
      )}
    </div>
  );
}
