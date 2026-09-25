"use client";

import { useQuery } from "@tanstack/react-query";
import { Section } from "@/components/ui/Section";
import { getFichaBasica } from "@/lib/docente";
import { getFichaDatosComplementarios } from "@/lib/fichas";
import type { FichaDatosBasicosOut } from "@/types";
import styles from "./FichaViewer.module.scss";

function FichaItem({ label, valor }: { label: string; valor: string }) {
  return (
    <div className={styles.fichaItem}>
      <span className={styles.fichaLabel}>{label}</span>
      <span className={styles.fichaValue}>{valor}</span>
    </div>
  );
}

function FichaResumen({ ficha }: { ficha: FichaDatosBasicosOut }) {
  const nombres = [ficha.primerNombre, ficha.segundoNombre]
    .filter(Boolean)
    .join(" ");
  const apellidos = [ficha.primerApellido, ficha.segundoApellido]
    .filter(Boolean)
    .join(" ");
  const identificacion = [ficha.tipoId, ficha.numId].filter(Boolean).join(" ");
  const sexo =
    ficha.sexo === "M" ? "Masculino" : ficha.sexo === "F" ? "Femenino" : ficha.sexo;

  return (
    <div className={styles.fichaSections}>
      <Section
        step="01"
        title="Identificación"
        subtitle="Datos personales del paciente"
      >
        <div className={styles.fichaGrid}>
          <FichaItem label="Identificación" valor={identificacion || "—"} />
          <FichaItem label="Nombres" valor={nombres || "—"} />
          <FichaItem label="Apellidos" valor={apellidos || "—"} />
          <FichaItem label="Sexo" valor={sexo} />
          <FichaItem label="Fecha de nacimiento" valor={ficha.fNacimiento} />
          <FichaItem label="Edad" valor={String(ficha.edad)} />
        </div>
      </Section>

      <Section step="02" title="Evento y notificación">
        <div className={styles.fichaGrid}>
          <FichaItem label="Código de evento" valor={ficha.codEvento} />
          <FichaItem
            label="Clasificación de caso"
            valor={String(ficha.clasificacionCaso)}
          />
          <FichaItem label="Estado" valor={ficha.estado} />
          <FichaItem
            label="Fecha de notificación"
            valor={ficha.fNotificacion}
          />
          <FichaItem label="Año" valor={String(ficha.anio)} />
          <FichaItem
            label="Semana epidemiológica"
            valor={String(ficha.semanaEpidemiologica)}
          />
          <FichaItem label="UPGD" valor={ficha.codUpgd} />
        </div>
      </Section>

      <Section step="03" title="Datos clínicos">
        <div className={styles.fichaGrid}>
          <FichaItem
            label="Hospitalizado"
            valor={ficha.hospitalizado ? "Sí" : "No"}
          />
          <FichaItem
            label="Condición final"
            valor={String(ficha.condicionFinal)}
          />
        </div>
      </Section>

      <Section step="04" title="Ubicación">
        <div className={styles.fichaGrid}>
          <FichaItem label="País" valor={ficha.paisOcurrencia} />
          <FichaItem label="Departamento" valor={ficha.dptoOcurrencia} />
          <FichaItem label="Municipio" valor={ficha.muniOcurrencia} />
          <FichaItem
            label="Área de ocurrencia"
            valor={String(ficha.areaOcurrencia)}
          />
        </div>
      </Section>
    </div>
  );
}

function humanizarEtiqueta(clave: string): string {
  const palabras = clave.replace(/_/g, " ").trim();
  if (!palabras) return clave;
  return palabras.charAt(0).toUpperCase() + palabras.slice(1);
}

function formatValorComplementario(valor: unknown): string {
  if (valor === null || valor === undefined) return "—";
  if (typeof valor === "boolean") return valor ? "Sí" : "No";
  if (typeof valor === "number" || typeof valor === "string") {
    const texto = String(valor).trim();
    return texto === "" ? "—" : texto;
  }
  return JSON.stringify(valor);
}

function DatosComplementariosResumen({
  contenido,
}: {
  contenido: Record<string, unknown>;
}) {
  const entradas = Object.entries(contenido);

  if (entradas.length === 0) {
    return (
      <Section step="05" title="Datos complementarios">
        <p className={styles.banner}>Sin datos complementarios.</p>
      </Section>
    );
  }

  return (
    <Section
      step="05"
      title="Datos complementarios"
      subtitle="Información complementaria del evento"
    >
      <div className={styles.fichaGrid}>
        {entradas.map(([clave, valor]) => (
          <FichaItem
            key={clave}
            label={humanizarEtiqueta(clave)}
            valor={formatValorComplementario(valor)}
          />
        ))}
      </div>
    </Section>
  );
}

export function FichaViewer({ fichaBasicaId }: { fichaBasicaId: number }) {
  const {
    data: ficha,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["ficha", "datos-basicos", fichaBasicaId],
    queryFn: () => getFichaBasica(fichaBasicaId),
  });

  const {
    data: complementaria,
    isLoading: complementariaLoading,
  } = useQuery({
    queryKey: ["ficha", "datos-complementarios", fichaBasicaId],
    queryFn: () => getFichaDatosComplementarios(fichaBasicaId),
  });

  return (
    <div>
      {isLoading && <p className={styles.banner}>Cargando ficha…</p>}
      {isError && (
        <p className={styles.errorBanner}>No se pudo cargar la ficha.</p>
      )}
      {ficha && (
        <>
          <FichaResumen ficha={ficha} />
          {complementariaLoading && (
            <p className={styles.banner}>
              Cargando datos complementarios…
            </p>
          )}
          {!complementariaLoading && (
            <DatosComplementariosResumen
              contenido={complementaria?.contenido ?? {}}
            />
          )}
        </>
      )}
    </div>
  );
}

export function FichaViewerModal({
  fichaBasicaId,
  onClose,
}: {
  fichaBasicaId: number;
  onClose: () => void;
}) {
  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ficha-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className={styles.modalHeader}>
          <h2 className={styles.modalTitle} id="ficha-modal-title">
            Ficha de datos básicos
          </h2>
          <button
            type="button"
            className={styles.modalClose}
            onClick={onClose}
            aria-label="Cerrar"
          >
            ×
          </button>
        </header>
        <div className={styles.modalBody}>
          <FichaViewer fichaBasicaId={fichaBasicaId} />
        </div>
      </div>
    </div>
  );
}
