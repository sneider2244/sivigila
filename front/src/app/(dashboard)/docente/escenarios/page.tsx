"use client";

import { useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { RadioYN } from "@/components/ui/RadioYN";
import { useUserStore } from "@/store/useUserStore";
import {
  asignarEscenario,
  createEscenario,
  evaluarFicha,
  getAsignaciones,
  getEscenarios,
} from "@/lib/docente";
import type {
  EscenarioAsignacion,
  EscenarioClinico,
  EvaluacionResult,
} from "@/types";
import styles from "./escenarios.module.scss";

const escenarioSchema = z
  .object({
    titulo: z.string().min(3, "El título debe tener al menos 3 caracteres"),
    descripcion: z
      .string()
      .min(3, "La descripción debe tener al menos 3 caracteres"),
    codEvento: z.string().min(1, "El código de evento es obligatorio"),
    datosEsperados: z.string().min(1, "Los datos esperados son obligatorios"),
    activo: z.boolean(),
  })
  .superRefine((data, ctx) => {
    try {
      const parsed = JSON.parse(data.datosEsperados);
      if (
        typeof parsed !== "object" ||
        parsed === null ||
        Array.isArray(parsed)
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          path: ["datosEsperados"],
          message: "Los datos esperados deben ser un objeto JSON",
        });
      }
    } catch {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["datosEsperados"],
        message: "Los datos esperados deben ser un JSON válido",
      });
    }
  });

type EscenarioFormValues = z.infer<typeof escenarioSchema>;

function formatDetail(detalle: unknown): string {
  return JSON.stringify(detalle, null, 2);
}

function EscenarioForm() {
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState<string | null>(null);

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
      datosEsperados: "",
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
    let datosEsperados: unknown;
    try {
      datosEsperados = JSON.parse(values.datosEsperados);
    } catch {
      setSubmitError("Los datos esperados deben ser un JSON válido");
      return;
    }
    createMutation.mutate(
      {
        titulo: values.titulo,
        descripcion: values.descripcion,
        codEvento: values.codEvento,
        datosEsperados,
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
          <Input
            id="descripcion"
            aria-invalid={Boolean(errors.descripcion)}
            placeholder="Situación clínica que debe resolver el estudiante"
            {...register("descripcion")}
          />
        </Field>
        <Field
          label="Código de evento"
          htmlFor="codEvento"
          error={errors.codEvento?.message}
        >
          <Input
            id="codEvento"
            aria-invalid={Boolean(errors.codEvento)}
            placeholder="Ej. 100"
            {...register("codEvento")}
          />
        </Field>
        <Field
          label="Datos esperados (JSON)"
          htmlFor="datosEsperados"
          error={errors.datosEsperados?.message}
          hint="Objeto JSON con los valores esperados de la ficha."
        >
          <textarea
            id="datosEsperados"
            className={styles.textarea}
            rows={5}
            aria-invalid={Boolean(errors.datosEsperados)}
            placeholder='{"clasificacion_caso": 2}'
            {...register("datosEsperados")}
          />
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

function EscenarioCard({
  escenario,
  onVerAsignaciones,
}: {
  escenario: EscenarioClinico;
  onVerAsignaciones: () => void;
}) {
  const queryClient = useQueryClient();
  const [estudianteId, setEstudianteId] = useState("");
  const [asignarError, setAsignarError] = useState<string | null>(null);
  const [asignarSuccess, setAsignarSuccess] = useState(false);

  const asignarMutation = useMutation({
    mutationFn: (input: { escenarioId: number; estudianteId: number }) =>
      asignarEscenario(input.escenarioId, input.estudianteId),
    onSuccess: () => {
      setEstudianteId("");
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

  const handleAsignar = () => {
    setAsignarError(null);
    setAsignarSuccess(false);
    const id = Number(estudianteId);
    if (!Number.isInteger(id) || id <= 0) {
      setAsignarError("Ingrese un ID de estudiante válido");
      return;
    }
    asignarMutation.mutate({ escenarioId: escenario.id, estudianteId: id });
  };

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
      <details className={styles.jsonDetails}>
        <summary>Datos esperados</summary>
        <pre className={styles.json}>
          {formatDetail(escenario.datosEsperados)}
        </pre>
      </details>
      <div className={styles.cardActions}>
        <div className={styles.assign}>
          <Input
            type="number"
            min={1}
            value={estudianteId}
            onChange={(e) => setEstudianteId(e.target.value)}
            placeholder="ID estudiante"
            aria-label={`ID de estudiante para ${escenario.titulo}`}
          />
          <button
            type="button"
            className={styles.button}
            onClick={handleAsignar}
            disabled={asignarMutation.isPending}
          >
            {asignarMutation.isPending ? "Asignando…" : "Asignar"}
          </button>
        </div>
        <button
          type="button"
          className={styles.buttonGhost}
          onClick={onVerAsignaciones}
        >
          Ver asignaciones
        </button>
      </div>
      {asignarError && <p className={styles.errorBanner}>{asignarError}</p>}
      {asignarSuccess && (
        <p className={styles.successBanner}>
          Estudiante asignado correctamente.
        </p>
      )}
    </article>
  );
}

function AsignacionRow({ asignacion }: { asignacion: EscenarioAsignacion }) {
  const [result, setResult] = useState<EvaluacionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const evaluarMutation = useMutation({
    mutationFn: (input: { fichaBasicaId: number; escenarioId: number }) =>
      evaluarFicha(input.fichaBasicaId, input.escenarioId),
    onSuccess: (data) => {
      setResult(data);
      setError(null);
    },
    onError: (err) => {
      setResult(null);
      setError(
        axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? "No se pudo evaluar la ficha")
          : "No se pudo evaluar la ficha",
      );
    },
  });

  const handleEvaluar = () => {
    if (asignacion.fichaBasicaId == null || asignacion.escenarioId == null) {
      return;
    }
    evaluarMutation.mutate({
      fichaBasicaId: asignacion.fichaBasicaId,
      escenarioId: asignacion.escenarioId,
    });
  };

  const puedeEvaluar =
    asignacion.fichaBasicaId != null && asignacion.escenarioId != null;

  return (
    <li className={styles.asignacion}>
      <div className={styles.asignacionInfo}>
        <span className={styles.asignacionEscenario}>
          {asignacion.escenarioTitulo}
        </span>
        <span className={styles.asignacionEstudiante}>
          {asignacion.estudianteNombre} ({asignacion.estudianteUsername})
        </span>
        <span className={styles.estado}>{asignacion.estado}</span>
      </div>
      {puedeEvaluar && (
        <button
          type="button"
          className={styles.button}
          onClick={handleEvaluar}
          disabled={evaluarMutation.isPending}
        >
          {evaluarMutation.isPending ? "Evaluando…" : "Evaluar"}
        </button>
      )}
      {result && (
        <div className={styles.resultado}>
          <p>
            Puntaje: <strong>{result.puntaje}</strong>
          </p>
          <p>
            Aciertos: {result.aciertos}/{result.total}
          </p>
          <pre className={styles.json}>{formatDetail(result.detalle)}</pre>
        </div>
      )}
      {error && <p className={styles.errorBanner}>{error}</p>}
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
              <AsignacionRow key={asignacion.id} asignacion={asignacion} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
