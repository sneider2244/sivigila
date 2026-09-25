"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Controller,
  useForm,
  useWatch,
  type Control,
  type FieldPath,
} from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RadioYN } from "@/components/ui/RadioYN";
import { createFichaDatosComplementarios } from "@/lib/fichas";
import type { FichaDatosComplementarios } from "@/types";
import styles from "./datos-complementarios.module.scss";

const COD_EVENTO = "100";

const AGENTES_AGRESORES = [
  { codigo: 1, nombre: "Bothrops (talla equis / mapaná)" },
  { codigo: 2, nombre: "Lachesis (verrugosa)" },
  { codigo: 3, nombre: "Crotalus (cascabel)" },
  { codigo: 4, nombre: "Micrurus (coral)" },
  { codigo: 5, nombre: "Serpiente no identificada" },
];

const MANIFESTACIONES_LOCALES: {
  name:
    | "contenido.manifestacionesLocales.edema"
    | "contenido.manifestacionesLocales.dolor"
    | "contenido.manifestacionesLocales.eritema"
    | "contenido.manifestacionesLocales.equimosis"
    | "contenido.manifestacionesLocales.flictenas"
    | "contenido.manifestacionesLocales.necrosisLocal";
  label: string;
}[] = [
  { name: "contenido.manifestacionesLocales.edema", label: "Edema" },
  { name: "contenido.manifestacionesLocales.dolor", label: "Dolor" },
  { name: "contenido.manifestacionesLocales.eritema", label: "Eritema" },
  { name: "contenido.manifestacionesLocales.equimosis", label: "Equimosis" },
  { name: "contenido.manifestacionesLocales.flictenas", label: "Flictenas" },
  {
    name: "contenido.manifestacionesLocales.necrosisLocal",
    label: "Necrosis local",
  },
];

const MANIFESTACIONES_SISTEMICAS: {
  name:
    | "contenido.manifestacionesSistemicas.nauseas"
    | "contenido.manifestacionesSistemicas.vomito"
    | "contenido.manifestacionesSistemicas.dolorAbdominal"
    | "contenido.manifestacionesSistemicas.bradicardia"
    | "contenido.manifestacionesSistemicas.hipotension"
    | "contenido.manifestacionesSistemicas.sangrado";
  label: string;
}[] = [
  { name: "contenido.manifestacionesSistemicas.nauseas", label: "Náuseas" },
  { name: "contenido.manifestacionesSistemicas.vomito", label: "Vómito" },
  {
    name: "contenido.manifestacionesSistemicas.dolorAbdominal",
    label: "Dolor abdominal",
  },
  {
    name: "contenido.manifestacionesSistemicas.bradicardia",
    label: "Bradicardia",
  },
  {
    name: "contenido.manifestacionesSistemicas.hipotension",
    label: "Hipotensión",
  },
  { name: "contenido.manifestacionesSistemicas.sangrado", label: "Sangrado" },
];

const COMPLICACIONES: {
  name:
    | "contenido.complicaciones.celulitis"
    | "contenido.complicaciones.necrosis"
    | "contenido.complicaciones.insuficienciaRenal"
    | "contenido.complicaciones.hipoxia";
  label: string;
}[] = [
  { name: "contenido.complicaciones.celulitis", label: "Celulitis" },
  { name: "contenido.complicaciones.necrosis", label: "Necrosis" },
  {
    name: "contenido.complicaciones.insuficienciaRenal",
    label: "Insuficiencia renal",
  },
  { name: "contenido.complicaciones.hipoxia", label: "Hipoxia" },
];

const datosComplementariosSchema = z.object({
  fichaBasicaId: z
    .number({ error: "El ID de la ficha básica es obligatorio" })
    .int("El ID de la ficha básica debe ser un número entero")
    .positive("El ID de la ficha básica debe ser positivo"),
  contenido: z.object({
    datosAccidente: z.object({
      fecha: z.string().min(1, "La fecha del accidente es obligatoria"),
      direccion: z.string().min(1, "La dirección es obligatoria"),
      agenteAgresor: z
        .number({ error: "Seleccione el agente agresor" })
        .int()
        .min(1),
    }),
    manifestacionesLocales: z.object({
      edema: z.boolean(),
      dolor: z.boolean(),
      eritema: z.boolean(),
      equimosis: z.boolean(),
      flictenas: z.boolean(),
      necrosisLocal: z.boolean(),
    }),
    manifestacionesSistemicas: z.object({
      nauseas: z.boolean(),
      vomito: z.boolean(),
      dolorAbdominal: z.boolean(),
      bradicardia: z.boolean(),
      hipotension: z.boolean(),
      sangrado: z.boolean(),
    }),
    complicaciones: z.object({
      celulitis: z.boolean(),
      necrosis: z.boolean(),
      insuficienciaRenal: z.boolean(),
      hipoxia: z.boolean(),
    }),
    atencionHospitalaria: z.object({
      empleoSuero: z
        .number({ error: "Indique si se empleó suero antiofídico" })
        .int()
        .min(1)
        .max(2),
      dosis: z.number().int().nullable(),
    }),
  }),
});

type DatosComplementariosFormValues = z.infer<
  typeof datosComplementariosSchema
>;

function YNChip({
  control,
  name,
  label,
  error,
}: {
  control: Control<DatosComplementariosFormValues>;
  name: FieldPath<DatosComplementariosFormValues>;
  label: string;
  error?: string;
}) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => (
        <RadioYN
          name={name}
          label={label}
          value={Boolean(field.value)}
          onChange={(value) => field.onChange(value)}
          error={error}
        />
      )}
    />
  );
}

function DatosComplementariosForm() {
  const searchParams = useSearchParams();
  const fichaBasicaIdParam = searchParams.get("fichaBasicaId");
  const parsedId = fichaBasicaIdParam ? Number(fichaBasicaIdParam) : NaN;
  const idFromQuery = Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null;

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DatosComplementariosFormValues>({
    resolver: zodResolver(datosComplementariosSchema),
    defaultValues: {
      fichaBasicaId: idFromQuery ?? undefined,
      contenido: {
        datosAccidente: {
          fecha: "",
          direccion: "",
          agenteAgresor: undefined,
        },
        manifestacionesLocales: {
          edema: false,
          dolor: false,
          eritema: false,
          equimosis: false,
          flictenas: false,
          necrosisLocal: false,
        },
        manifestacionesSistemicas: {
          nauseas: false,
          vomito: false,
          dolorAbdominal: false,
          bradicardia: false,
          hipotension: false,
          sangrado: false,
        },
        complicaciones: {
          celulitis: false,
          necrosis: false,
          insuficienciaRenal: false,
          hipoxia: false,
        },
        atencionHospitalaria: {
          empleoSuero: undefined,
          dosis: null,
        },
      },
    },
  });

  const empleoSuero = useWatch({
    control,
    name: "contenido.atencionHospitalaria.empleoSuero",
  });

  const onSubmit = async (values: DatosComplementariosFormValues) => {
    setSubmitError(null);
    setSuccess(false);

    const ficha: FichaDatosComplementarios = {
      fichaBasicaId: values.fichaBasicaId,
      codEvento: COD_EVENTO,
      contenido: {
        datosAccidente: {
          fecha: values.contenido.datosAccidente.fecha,
          direccion: values.contenido.datosAccidente.direccion,
          agenteAgresor: values.contenido.datosAccidente.agenteAgresor,
        },
        manifestacionesLocales: {
          edema: values.contenido.manifestacionesLocales.edema,
          dolor: values.contenido.manifestacionesLocales.dolor,
          eritema: values.contenido.manifestacionesLocales.eritema,
          equimosis: values.contenido.manifestacionesLocales.equimosis,
          flictenas: values.contenido.manifestacionesLocales.flictenas,
          necrosisLocal: values.contenido.manifestacionesLocales.necrosisLocal,
        },
        manifestacionesSistemicas: {
          nauseas: values.contenido.manifestacionesSistemicas.nauseas,
          vomito: values.contenido.manifestacionesSistemicas.vomito,
          dolorAbdominal: values.contenido.manifestacionesSistemicas.dolorAbdominal,
          bradicardia: values.contenido.manifestacionesSistemicas.bradicardia,
          hipotension: values.contenido.manifestacionesSistemicas.hipotension,
          sangrado: values.contenido.manifestacionesSistemicas.sangrado,
        },
        complicaciones: {
          celulitis: values.contenido.complicaciones.celulitis,
          necrosis: values.contenido.complicaciones.necrosis,
          insuficienciaRenal: values.contenido.complicaciones.insuficienciaRenal,
          hipoxia: values.contenido.complicaciones.hipoxia,
        },
        atencionHospitalaria: {
          empleoSuero: values.contenido.atencionHospitalaria.empleoSuero,
          dosis: values.contenido.atencionHospitalaria.dosis,
        },
      },
    };

    try {
      await createFichaDatosComplementarios(ficha);
      setSuccess(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setSubmitError(
          err.response?.data?.detail ?? "No se pudo guardar la ficha.",
        );
      } else {
        setSubmitError("No se pudo guardar la ficha.");
      }
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Datos Complementarios</h1>
        <p className={styles.subtitle}>
          Accidente ofídico — manifestaciones clínicas y atención hospitalaria.
        </p>
      </header>

      {!idFromQuery && (
        <p className={styles.errorBanner}>
          No se indicó el ID de la ficha básica. Ingresalo en el campo
          correspondiente o accedé con el parámetro{" "}
          <code>?fichaBasicaId=&#123;id&#125;</code>.
        </p>
      )}

      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Ficha básica asociada</h2>
          <Field
            label="ID de la ficha básica"
            htmlFor="fichaBasicaId"
            error={errors.fichaBasicaId?.message}
          >
            <Input
              id="fichaBasicaId"
              type="number"
              aria-invalid={Boolean(errors.fichaBasicaId)}
              readOnly={idFromQuery !== null}
              placeholder="Identificador de la ficha de datos básicos"
              {...register("fichaBasicaId", {
                setValueAs: (value) => (value === "" ? undefined : Number(value)),
              })}
            />
          </Field>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Datos del accidente</h2>
          <div className={styles.grid}>
            <Field
              label="Fecha del accidente"
              htmlFor="contenido.datosAccidente.fecha"
              error={errors.contenido?.datosAccidente?.fecha?.message}
            >
              <Input
                id="contenido.datosAccidente.fecha"
                type="date"
                aria-invalid={Boolean(
                  errors.contenido?.datosAccidente?.fecha,
                )}
                {...register("contenido.datosAccidente.fecha")}
              />
            </Field>
            <Field
              label="Agente agresor"
              htmlFor="contenido.datosAccidente.agenteAgresor"
              error={errors.contenido?.datosAccidente?.agenteAgresor?.message}
            >
              <Select
                id="contenido.datosAccidente.agenteAgresor"
                aria-invalid={Boolean(
                  errors.contenido?.datosAccidente?.agenteAgresor,
                )}
                {...register("contenido.datosAccidente.agenteAgresor", {
                  setValueAs: (value) =>
                    value === "" ? undefined : Number(value),
                })}
              >
                <option value="">Seleccione…</option>
                {AGENTES_AGRESORES.map((a) => (
                  <option key={a.codigo} value={a.codigo}>
                    {a.nombre}
                  </option>
                ))}
              </Select>
            </Field>
          </div>
          <Field
            label="Dirección del accidente"
            htmlFor="contenido.datosAccidente.direccion"
            error={errors.contenido?.datosAccidente?.direccion?.message}
          >
            <Input
              id="contenido.datosAccidente.direccion"
              aria-invalid={Boolean(
                errors.contenido?.datosAccidente?.direccion,
              )}
              placeholder="Lugar de la agresión"
              {...register("contenido.datosAccidente.direccion")}
            />
          </Field>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Manifestaciones locales</h2>
          <div className={styles.chips}>
            {MANIFESTACIONES_LOCALES.map((m) => (
              <YNChip
                key={m.name}
                control={control}
                name={m.name}
                label={m.label}
              />
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Manifestaciones sistémicas</h2>
          <div className={styles.chips}>
            {MANIFESTACIONES_SISTEMICAS.map((m) => (
              <YNChip
                key={m.name}
                control={control}
                name={m.name}
                label={m.label}
              />
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Complicaciones</h2>
          <div className={styles.chips}>
            {COMPLICACIONES.map((c) => (
              <YNChip
                key={c.name}
                control={control}
                name={c.name}
                label={c.label}
              />
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Atención hospitalaria</h2>
          <div className={styles.grid}>
            <Field
              label="¿Se empleó suero antiofídico?"
              htmlFor="contenido.atencionHospitalaria.empleoSuero"
              error={
                errors.contenido?.atencionHospitalaria?.empleoSuero?.message
              }
            >
              <Select
                id="contenido.atencionHospitalaria.empleoSuero"
                aria-invalid={Boolean(
                  errors.contenido?.atencionHospitalaria?.empleoSuero,
                )}
                {...register("contenido.atencionHospitalaria.empleoSuero", {
                  setValueAs: (value) =>
                    value === "" ? undefined : Number(value),
                })}
              >
                <option value="">Seleccione…</option>
                <option value="1">Sí</option>
                <option value="2">No</option>
              </Select>
            </Field>
            {empleoSuero === 1 && (
              <Field
                label="Número de dosis"
                htmlFor="contenido.atencionHospitalaria.dosis"
                error={errors.contenido?.atencionHospitalaria?.dosis?.message}
              >
                <Input
                  id="contenido.atencionHospitalaria.dosis"
                  type="number"
                  min={0}
                  aria-invalid={Boolean(
                    errors.contenido?.atencionHospitalaria?.dosis,
                  )}
                  {...register("contenido.atencionHospitalaria.dosis", {
                    setValueAs: (value) =>
                      value === "" ? null : Number(value),
                  })}
                />
              </Field>
            )}
          </div>
        </section>

        {submitError && <p className={styles.errorBanner}>{submitError}</p>}
        {success && (
          <p className={styles.successBanner}>
            Ficha de datos complementarios guardada correctamente.
          </p>
        )}

        <button
          type="submit"
          className={styles.submit}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Guardando…" : "Guardar ficha"}
        </button>
      </form>
    </div>
  );
}

export default function DatosComplementariosPage() {
  return (
    <Suspense fallback={<p className={styles.loading}>Cargando…</p>}>
      <DatosComplementariosForm />
    </Suspense>
  );
}
