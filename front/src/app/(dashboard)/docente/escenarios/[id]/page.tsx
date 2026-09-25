"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Section } from "@/components/ui/Section";
import { EstudianteSelector } from "@/components/docente/EstudianteSelector";
import { FichaViewerModal } from "@/components/ficha/FichaViewer";
import { useUserStore } from "@/store/useUserStore";
import {
  getAsignacionesPorEscenario,
  getEscenario,
} from "@/lib/docente";
import type { EscenarioAsignacion } from "@/types";
import styles from "./detalle.module.scss";

type Tab = "asignaciones" | "asignar";

function AsignacionRow({ asignacion }: { asignacion: EscenarioAsignacion }) {
  const [verFicha, setVerFicha] = useState(false);
  const identificacion = asignacion.estudianteNumeroIdentificacion;

  return (
    <li className={styles.asignacion}>
      <div className={styles.asignacionInfo}>
        <span className={styles.asignacionEstudiante}>
          <strong>{asignacion.estudianteNombre}</strong> (
          {asignacion.estudianteUsername})
          {identificacion ? ` · CC ${identificacion}` : ""}
        </span>
        <span className={styles.estado}>{asignacion.estado}</span>
      </div>
      {asignacion.fichaBasicaId != null && (
        <button
          type="button"
          className={styles.buttonGhost}
          onClick={() => setVerFicha(true)}
        >
          Ver ficha
        </button>
      )}
      {verFicha && asignacion.fichaBasicaId != null && (
        <FichaViewerModal
          fichaBasicaId={asignacion.fichaBasicaId}
          onClose={() => setVerFicha(false)}
        />
      )}
    </li>
  );
}

export default function DetalleEscenarioPage() {
  const user = useUserStore((state) => state.user);
  const isDocente = user?.rol === "DOCENTE";

  const params = useParams<{ id: string }>();
  const escenarioId = Number(params?.id);

  const [tab, setTab] = useState<Tab>("asignaciones");

  const {
    data: escenario,
    isLoading: escenarioLoading,
    isError: escenarioError,
  } = useQuery({
    queryKey: ["docente", "escenarios", escenarioId],
    queryFn: () => getEscenario(escenarioId),
    enabled: isDocente && Number.isInteger(escenarioId) && escenarioId > 0,
  });

  const {
    data: asignaciones = [],
    isLoading: asignacionesLoading,
    isError: asignacionesError,
  } = useQuery({
    queryKey: ["docente", "escenarios", escenarioId, "asignaciones"],
    queryFn: () => getAsignacionesPorEscenario(escenarioId),
    enabled: isDocente && Number.isInteger(escenarioId) && escenarioId > 0,
  });

  if (!isDocente) {
    return (
      <div className={styles.page}>
        <div className={styles.accessDenied}>Acceso solo para docentes</div>
      </div>
    );
  }

  if (escenarioLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.banner}>Cargando escenario…</div>
      </div>
    );
  }

  if (escenarioError || !escenario) {
    return (
      <div className={styles.page}>
        <div className={styles.actions}>
          <Link href="/docente/escenarios" className={styles.buttonGhost}>
            Volver
          </Link>
        </div>
        <div className={styles.accessDenied}>Escenario no encontrado.</div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.actions}>
          <Link href="/docente/escenarios" className={styles.buttonGhost}>
            Volver
          </Link>
        </div>
        <h1 className={styles.title}>{escenario.titulo}</h1>
        <p className={styles.subtitle}>{escenario.descripcion}</p>
        <div className={styles.metaRow}>
          <span className={styles.cardMeta}>
            Evento: <strong>{escenario.codEvento}</strong>
          </span>
          <span
            className={
              escenario.activo ? styles.badgeActive : styles.badgeInactive
            }
          >
            {escenario.activo ? "Activo" : "Inactivo"}
          </span>
        </div>
      </header>

      <div className={styles.tabs} role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === "asignaciones"}
          className={`${styles.tab} ${
            tab === "asignaciones" ? styles.tabActive : ""
          }`}
          onClick={() => setTab("asignaciones")}
        >
          Asignaciones ({asignaciones.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "asignar"}
          className={`${styles.tab} ${
            tab === "asignar" ? styles.tabActive : ""
          }`}
          onClick={() => setTab("asignar")}
        >
          Asignar estudiantes
        </button>
      </div>

      {tab === "asignar" ? (
        <Section
          step="01"
          title="Asignar estudiantes"
          subtitle="Buscá y seleccioná estudiantes para asignarles este escenario"
        >
          <EstudianteSelector escenario={escenario} />
        </Section>
      ) : (
        <Section
          step="02"
          title={`Asignaciones (${asignaciones.length})`}
          subtitle="Estudiantes asignados a este escenario"
        >
          {asignacionesLoading && (
            <p className={styles.banner}>Cargando asignaciones…</p>
          )}
          {asignacionesError && (
            <p className={styles.errorBanner}>
              No se pudieron cargar las asignaciones.
            </p>
          )}
          {!asignacionesLoading &&
            !asignacionesError &&
            asignaciones.length === 0 && (
              <p className={styles.banner}>
                Aún no hay estudiantes asignados a este escenario.
              </p>
            )}
          {!asignacionesLoading && !asignacionesError && (
            <ul className={styles.asignacionList}>
              {asignaciones.map((asignacion) => (
                <AsignacionRow key={asignacion.id} asignacion={asignacion} />
              ))}
            </ul>
          )}
        </Section>
      )}
    </div>
  );
}
