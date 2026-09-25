"use client";

import { useMemo, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RadioYN } from "@/components/ui/RadioYN";
import { useUserStore } from "@/store/useUserStore";
import {
  asignarEscenario,
  createEscenario,
  getAsignaciones,
  getEscenarios,
  getEstudiantes,
  getFichaBasica,
} from "@/lib/docente";
import { getEventos } from "@/lib/catalogos";
import type {
  EscenarioAsignacion,
  EscenarioClinico,
  EstudianteDocente,
  FichaDatosBasicosOut,
} from "@/types";
import styles from "./escenarios.module.scss";

const escenarioSchema = z.object({
  titulo: z.string().min(3, "El título debe tener al menos 3 caracteres"),
  descripcion: z
    .string()
    .min(3, "La descripción debe tener al menos 3 caracteres"),
  codEvento: z.string().min(1, "El código de evento es obligatorio"),
  activo: z.boolean(),
});

type EscenarioFormValues = z.infer<typeof escenarioSchema>;

function EscenarioForm() {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { data: eventos = [] } = useQuery({
    queryKey: ["catalogos", "eventos"],
    queryFn: getEventos,
  });

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<EscenarioFormValues>({
    resolver: zodResolver(escenarioSchema),
    defaultValues: {
      titulo: "",
      descripcion: "",
      codEvento: "",
      activo: true,
    },
  });

  const createMutation = useMutation({
    mutationFn: createEscenario,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["docente", "escenarios"] });
      reset();
    },
  });

  const onSubmit = (values: EscenarioFormValues) => {
    setSubmitError(null);
    createMutation.mutate(
      {
        titulo: values.titulo,
        descripcion: values.descripcion,
        codEvento: values.codEvento,
        activo: values.activo,
      },
      {
        onError: (err) => {
          setSubmitError(
            axios.isAxiosError(err)
              ? (err.response?.data?.detail ?? "No se pudo crear el escenario")
              : "No se pudo crear el escenario",
          );
        },
      },
    );
  };

  return (
    <section className={styles.section}>
      <h2 className={styles.sectionTitle}>Crear escenario</h2>
      <form
        className={styles.form}
        onSubmit={handleSubmit(onSubmit)}
        noValidate
      >
        <Field
          label="Título"
          htmlFor="titulo"
          error={errors.titulo?.message}
        >
          <Input
            id="titulo"
            aria-invalid={Boolean(errors.titulo)}
            placeholder="Ej. Accidente ofídico — caso leve"
            {...register("titulo")}
          />
        </Field>
        <Field
          label="Descripción"
          htmlFor="descripcion"
          error={errors.descripcion?.message}
        >
          <textarea
            id="descripcion"
            className={styles.textarea}
            rows={4}
            aria-invalid={Boolean(errors.descripcion)}
            placeholder="Situación clínica que debe resolver el estudiante, p. ej. Reporte de fiebre amarilla, menor de 12 años…"
            {...register("descripcion")}
          />
        </Field>
        <Field
          label="Evento"
          htmlFor="codEvento"
          error={errors.codEvento?.message}
        >
          <Select
            id="codEvento"
            aria-invalid={Boolean(errors.codEvento)}
            {...register("codEvento")}
          >
            <option value="">Seleccione…</option>
            {eventos.map((evento) => (
              <option key={evento.codigo} value={evento.codigo}>
                {evento.nombre} ({evento.codigo})
              </option>
            ))}
          </Select>
        </Field>
        <Controller
          name="activo"
          control={control}
          render={({ field }) => (
            <RadioYN
              name="activo"
              label="¿El escenario está activo?"
              value={field.value}
              onChange={field.onChange}
            />
          )}
        />
        {submitError && <p className={styles.errorBanner}>{submitError}</p>}
        {createMutation.isSuccess && (
          <p className={styles.successBanner}>Escenario creado correctamente.</p>
        )}
        <button
          type="submit"
          className={styles.submit}
          disabled={isSubmitting || createMutation.isPending}
        >
          {createMutation.isPending ? "Creando…" : "Crear escenario"}
        </button>
      </form>
    </section>
  );
}

function EstudianteSelector({
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
      queryClient.invalidateQueries({ queryKey: ["docente", "asignaciones"] });
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

function EscenarioCard({
  escenario,
  onVerAsignaciones,
}: {
  escenario: EscenarioClinico;
  onVerAsignaciones: () => void;
}) {
  return (
    <article className={styles.card}>
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
      <EstudianteSelector escenario={escenario} />
      <div className={styles.cardActions}>
        <button
          type="button"
          className={styles.buttonGhost}
          onClick={onVerAsignaciones}
        >
          Ver asignaciones
        </button>
      </div>
    </article>
  );
}

function FichaBasicaModal({
  fichaBasicaId,
  onClose,
}: {
  fichaBasicaId: number;
  onClose: () => void;
}) {
  const {
    data: ficha,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["ficha", "datos-basicos", fichaBasicaId],
    queryFn: () => getFichaBasica(fichaBasicaId),
  });

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
          {isLoading && <p className={styles.banner}>Cargando ficha…</p>}
          {isError && (
            <p className={styles.errorBanner}>No se pudo cargar la ficha.</p>
          )}
          {ficha && <FichaResumen ficha={ficha} />}
        </div>
      </div>
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

  const filas: { label: string; valor: string }[] = [
    { label: "Número de identificación", valor: ficha.numId },
    { label: "Nombres", valor: nombres || "—" },
    { label: "Apellidos", valor: apellidos || "—" },
    { label: "Código de evento", valor: ficha.codEvento },
    { label: "Clasificación de caso", valor: String(ficha.clasificacionCaso) },
    {
      label: "Hospitalizado",
      valor: ficha.hospitalizado ? "Sí" : "No",
    },
    { label: "Condición final", valor: String(ficha.condicionFinal) },
    { label: "Estado", valor: ficha.estado },
    { label: "Edad", valor: String(ficha.edad) },
    { label: "Sexo", valor: ficha.sexo },
    { label: "Fecha de nacimiento", valor: ficha.fNacimiento },
    { label: "Año", valor: String(ficha.anio) },
    {
      label: "Semana epidemiológica",
      valor: String(ficha.semanaEpidemiologica),
    },
    { label: "UPGD", valor: ficha.codUpgd },
  ];

  return (
    <dl className={styles.fichaList}>
      {filas.map((fila) => (
        <div key={fila.label} className={styles.fichaRow}>
          <dt className={styles.fichaLabel}>{fila.label}</dt>
          <dd className={styles.fichaValue}>{fila.valor}</dd>
        </div>
      ))}
    </dl>
  );
}

function AsignacionRow({
  asignacion,
  numeroIdentificacion,
}: {
  asignacion: EscenarioAsignacion;
  numeroIdentificacion: string | null;
}) {
  const [verFicha, setVerFicha] = useState(false);

  return (
    <li className={styles.asignacion}>
      <div className={styles.asignacionInfo}>
        <span className={styles.asignacionEscenario}>
          {asignacion.escenarioTitulo}
        </span>
        <span className={styles.asignacionEstudiante}>
          {asignacion.estudianteNombre} ({asignacion.estudianteUsername})
          {numeroIdentificacion ? ` · CC ${numeroIdentificacion}` : ""}
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
        <FichaBasicaModal
          fichaBasicaId={asignacion.fichaBasicaId}
          onClose={() => setVerFicha(false)}
        />
      )}
    </li>
  );
}

export default function DocenteEscenariosPage() {
  const user = useUserStore((state) => state.user);
  const asignacionesRef = useRef<HTMLElement>(null);

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

  const {
    data: asignaciones = [],
    isLoading: asignacionesLoading,
    isError: asignacionesError,
  } = useQuery({
    queryKey: ["docente", "asignaciones"],
    queryFn: getAsignaciones,
    enabled: isDocente,
  });

  const { data: estudiantes = [] } = useQuery({
    queryKey: ["docente", "estudiantes", ""],
    queryFn: () => getEstudiantes(),
    enabled: isDocente,
  });

  const numeroIdentificacionPorEstudiante = useMemo(() => {
    const map = new Map<number, string | null>();
    for (const estudiante of estudiantes) {
      map.set(estudiante.id, estudiante.numeroIdentificacion);
    }
    return map;
  }, [estudiantes]);

  const scrollToAsignaciones = () => {
    asignacionesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

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
        <h1 className={styles.title}>Dashboard del Docente</h1>
        <p className={styles.subtitle}>
          Gestión de escenarios clínicos, asignación de estudiantes y
          evaluación de fichas.
        </p>
      </header>

      <EscenarioForm />

      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>Escenarios</h2>
        {escenariosLoading && <p className={styles.banner}>Cargando escenarios…</p>}
        {escenariosError && (
          <p className={styles.errorBanner}>No se pudieron cargar los escenarios.</p>
        )}
        {!escenariosLoading && !escenariosError && escenarios.length === 0 && (
          <p className={styles.banner}>No hay escenarios creados todavía.</p>
        )}
        {!escenariosLoading && !escenariosError && (
          <div className={styles.list}>
            {escenarios.map((escenario) => (
              <EscenarioCard
                key={escenario.id}
                escenario={escenario}
                onVerAsignaciones={scrollToAsignaciones}
              />
            ))}
          </div>
        )}
      </section>

      <section className={styles.section} ref={asignacionesRef}>
        <h2 className={styles.sectionTitle}>Asignaciones</h2>
        {asignacionesLoading && <p className={styles.banner}>Cargando asignaciones…</p>}
        {asignacionesError && (
          <p className={styles.errorBanner}>No se pudieron cargar las asignaciones.</p>
        )}
        {!asignacionesLoading && !asignacionesError && asignaciones.length === 0 && (
          <p className={styles.banner}>No hay asignaciones registradas.</p>
        )}
        {!asignacionesLoading && !asignacionesError && (
          <ul className={styles.asignacionList}>
            {asignaciones.map((asignacion) => (
              <AsignacionRow
                key={asignacion.id}
                asignacion={asignacion}
                numeroIdentificacion={
                  numeroIdentificacionPorEstudiante.get(asignacion.estudianteId) ??
                  asignacion.numeroIdentificacion ??
                  null
                }
              />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
