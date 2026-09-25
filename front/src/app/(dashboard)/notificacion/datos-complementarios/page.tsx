"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Section } from "@/components/ui/Section";
import { CaseBanner } from "@/components/ficha/CaseBanner";
import { createFichaDatosComplementarios } from "@/lib/fichas";
import { entregarEscenario } from "@/lib/estudiante";
import { useFormDraft } from "@/hooks/useFormDraft";
import styles from "./datos-complementarios.module.scss";

const COD_EVENTO = "100";

const datosComplementariosSchema = z.object({
  ficha_basica_id: z
    .number({ error: "El ID de la ficha básica es obligatorio" })
    .int("El ID de la ficha básica debe ser un número entero")
    .positive("El ID de la ficha básica debe ser positivo"),
  fecha_evento: z.string().optional(),
  lugar: z.string().optional(),
  descripcion: z.string().optional(),
});

type DatosComplementariosFormValues = z.infer<
  typeof datosComplementariosSchema
>;

function DatosComplementariosForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const fichaBasicaIdParam = searchParams.get("ficha_basica_id");
  const parsedId = fichaBasicaIdParam ? Number(fichaBasicaIdParam) : NaN;
  const idFromQuery = Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null;

  const asignacionIdParam = searchParams.get("asignacion_id");
  const parsedAsignacionId = asignacionIdParam ? Number(asignacionIdParam) : NaN;
  const asignacionId =
    Number.isInteger(parsedAsignacionId) && parsedAsignacionId > 0
      ? parsedAsignacionId
      : null;

  const codEventoParam = searchParams.get("cod_evento");
  const codEvento = codEventoParam?.trim() || COD_EVENTO;

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DatosComplementariosFormValues>({
    resolver: zodResolver(datosComplementariosSchema),
    defaultValues: {
      ficha_basica_id: idFromQuery ?? undefined,
      fecha_evento: "",
      lugar: "",
      descripcion: "",
    },
  });

  const formValues = useWatch({ control }) as DatosComplementariosFormValues;
  const { clear: clearDraft } = useFormDraft<DatosComplementariosFormValues>(
    asignacionId != null
      ? `sivigila-draft-complementaria-${asignacionId}`
      : null,
    formValues,
    (v) => reset(v),
  );

  const onSubmit = async (values: DatosComplementariosFormValues) => {
    setSubmitError(null);
    setSuccess(false);

    try {
      await createFichaDatosComplementarios({
        fichaBasicaId: values.ficha_basica_id,
        codEvento,
        contenido: {
          fecha_evento: values.fecha_evento ?? null,
          lugar: values.lugar ?? null,
          descripcion: values.descripcion ?? null,
        },
      });

      if (asignacionId != null) {
        await entregarEscenario(asignacionId, values.ficha_basica_id);
        clearDraft();
        const params = new URLSearchParams({
          ficha_basica_id: String(values.ficha_basica_id),
          asignacion_id: String(asignacionId),
        });
        router.replace(`/notificacion/resumen?${params.toString()}`);
        return;
      }
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
          Información complementaria del evento notificado.
        </p>
      </header>

      {asignacionId != null && <CaseBanner asignacionId={asignacionId} />}

      {!idFromQuery && (
        <p className={styles.errorBanner}>
          No se indicó el ID de la ficha básica. Ingresalo en el campo
          correspondiente o accedé con el parámetro{" "}
          <code>?ficha_basica_id=&#123;id&#125;</code>.
        </p>
      )}

      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        <Section
          step="01"
          title="Ficha básica asociada"
          subtitle="Relación con la ficha de datos básicos del caso"
        >
          <Field
            label="ID de la ficha básica"
            htmlFor="ficha_basica_id"
            error={errors.ficha_basica_id?.message}
          >
            <Input
              id="ficha_basica_id"
              type="number"
              aria-invalid={Boolean(errors.ficha_basica_id)}
              readOnly={idFromQuery !== null}
              placeholder="Identificador de la ficha de datos básicos"
              {...register("ficha_basica_id", {
                setValueAs: (value) => (value === "" ? undefined : Number(value)),
              })}
            />
          </Field>
        </Section>

        <Section
          step="02"
          title="Datos del evento"
          subtitle="Circunstancias y contexto del evento notificado"
        >
          <div className={styles.grid}>
            <Field
              label="Fecha del evento"
              htmlFor="fecha_evento"
              error={errors.fecha_evento?.message}
            >
              <Input
                id="fecha_evento"
                type="date"
                aria-invalid={Boolean(errors.fecha_evento)}
                {...register("fecha_evento")}
              />
            </Field>
            <Field
              label="Lugar"
              htmlFor="lugar"
              error={errors.lugar?.message}
            >
              <Input
                id="lugar"
                aria-invalid={Boolean(errors.lugar)}
                placeholder="Lugar donde ocurrió el evento"
                {...register("lugar")}
              />
            </Field>
          </div>
        </Section>

        <Section
          step="03"
          title="Hallazgos clínicos"
          subtitle="Descripción en lenguaje natural del cuadro clínico"
        >
          <Field
            label="Descripción"
            htmlFor="descripcion"
            error={errors.descripcion?.message}
          >
            <textarea
              id="descripcion"
              className={styles.textarea}
              rows={5}
              aria-invalid={Boolean(errors.descripcion)}
              placeholder="Describa los signos, síntomas y hallazgos relevantes…"
              {...register("descripcion")}
            />
          </Field>
        </Section>

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
