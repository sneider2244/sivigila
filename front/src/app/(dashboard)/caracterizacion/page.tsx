"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RadioYN } from "@/components/ui/RadioYN";
import { createUpgd, getUpgd, updateUpgd } from "@/lib/upgd";
import type { NivelComplejidad, UpgdCaracterizacion } from "@/types";
import styles from "./caracterizacion.module.scss";

const DEPARTAMENTOS = [
  { codigo: "05", nombre: "Antioquia" },
  { codigo: "11", nombre: "Bogotá D.C." },
  { codigo: "76", nombre: "Valle del Cauca" },
];

const MUNICIPIOS = [
  { codigo: "05001", nombre: "Medellín" },
  { codigo: "11001", nombre: "Bogotá D.C." },
  { codigo: "76001", nombre: "Cali" },
];

const caracterizacionSchema = z
  .object({
    codPrestador: z
      .string()
      .length(12, "El código del prestador debe tener 12 caracteres"),
    razonSocial: z
      .string()
      .min(3, "La razón social debe tener al menos 3 caracteres"),
    nit: z.string().min(1, "El NIT es obligatorio"),
    nivelComplejidad: z
      .number({ error: "Seleccione el nivel de complejidad" })
      .int()
      .min(1, "Seleccione el nivel de complejidad")
      .max(4),
    cove: z.boolean(),
    unidadAnalisis: z.boolean(),
    internet: z.boolean(),
    activo: z.boolean(),
    departamentoCodigo: z.string().nullable(),
    municipioCodigo: z.string().nullable(),
  })
  .superRefine((data, ctx) => {
    if (data.nivelComplejidad >= 3 && !data.unidadAnalisis) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["unidadAnalisis"],
        message:
          "Una UPGD de nivel 3 o 4 debe contar con unidad de análisis",
      });
    }
  });

type CaracterizacionFormValues = z.infer<typeof caracterizacionSchema>;

function CaracterizacionForm() {
  const searchParams = useSearchParams();
  const codPrestador = searchParams.get("codPrestador");
  const isEditing = Boolean(codPrestador);

  const [loading, setLoading] = useState(isEditing);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CaracterizacionFormValues>({
    resolver: zodResolver(caracterizacionSchema),
    defaultValues: {
      codPrestador: "",
      razonSocial: "",
      nit: "",
      cove: false,
      unidadAnalisis: false,
      internet: false,
      activo: true,
      departamentoCodigo: null,
      municipioCodigo: null,
    },
  });

  useEffect(() => {
    if (!codPrestador) return;
    let cancelled = false;

    getUpgd(codPrestador)
      .then((upgd) => {
        if (cancelled) return;
        reset({
          codPrestador: upgd.codPrestador,
          razonSocial: upgd.razonSocial,
          nit: upgd.nit,
          nivelComplejidad: upgd.nivelComplejidad,
          cove: upgd.cove,
          unidadAnalisis: upgd.unidadAnalisis,
          internet: upgd.internet,
          activo: upgd.activo,
          departamentoCodigo: upgd.departamentoCodigo,
          municipioCodigo: upgd.municipioCodigo,
        });
      })
      .catch(() => {
        if (!cancelled) {
          setLoadError("No se pudo cargar la UPGD solicitada.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [codPrestador, reset]);

  const onSubmit = async (values: CaracterizacionFormValues) => {
    setSubmitError(null);
    setSuccess(false);

    const payload: UpgdCaracterizacion = {
      codPrestador: values.codPrestador,
      razonSocial: values.razonSocial,
      nit: values.nit,
      nivelComplejidad: values.nivelComplejidad as NivelComplejidad,
      cove: values.cove,
      unidadAnalisis: values.unidadAnalisis,
      internet: values.internet,
      activo: values.activo,
      departamentoCodigo: values.departamentoCodigo || null,
      municipioCodigo: values.municipioCodigo || null,
    };

    try {
      if (isEditing && codPrestador) {
        await updateUpgd(codPrestador, payload);
      } else {
        await createUpgd(payload);
      }
      setSuccess(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setSubmitError(
          err.response?.data?.detail ?? "No se pudo guardar la UPGD.",
        );
      } else {
        setSubmitError("No se pudo guardar la UPGD.");
      }
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Caracterización UPGD</h1>
        <p className={styles.subtitle}>
          Registro de la información institucional de la unidad primaria
          generadora de datos.
        </p>
      </header>

      {loading && <p className={styles.banner}>Cargando UPGD…</p>}
      {loadError && <p className={styles.errorBanner}>{loadError}</p>}

      {!loading && !loadError && (
        <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Información del prestador</h2>
            <div className={styles.grid}>
              <Field
                label="Código del prestador"
                htmlFor="codPrestador"
                error={errors.codPrestador?.message}
                hint={isEditing ? "El código no es editable en modo edición." : undefined}
              >
                <Input
                  id="codPrestador"
                  maxLength={12}
                  disabled={isEditing}
                  aria-invalid={Boolean(errors.codPrestador)}
                  placeholder="12 caracteres"
                  {...register("codPrestador")}
                />
              </Field>
              <Field
                label="NIT"
                htmlFor="nit"
                error={errors.nit?.message}
              >
                <Input
                  id="nit"
                  aria-invalid={Boolean(errors.nit)}
                  placeholder="900123456-7"
                  {...register("nit")}
                />
              </Field>
            </div>
            <Field
              label="Razón social"
              htmlFor="razonSocial"
              error={errors.razonSocial?.message}
            >
              <Input
                id="razonSocial"
                aria-invalid={Boolean(errors.razonSocial)}
                placeholder="E.S.E. Hospital …"
                {...register("razonSocial")}
              />
            </Field>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Caracterización</h2>
            <Field
              label="Nivel de complejidad"
              htmlFor="nivelComplejidad"
              error={errors.nivelComplejidad?.message}
            >
              <Select
                id="nivelComplejidad"
                aria-invalid={Boolean(errors.nivelComplejidad)}
                {...register("nivelComplejidad", {
                  setValueAs: (value) =>
                    value === "" ? undefined : Number(value),
                })}
              >
                <option value="">Seleccione…</option>
                <option value="1">Nivel 1 — Baja complejidad</option>
                <option value="2">Nivel 2 — Media complejidad</option>
                <option value="3">Nivel 3 — Alta complejidad</option>
                <option value="4">Nivel 4 — Máxima complejidad</option>
              </Select>
            </Field>

            <Controller
              name="cove"
              control={control}
              render={({ field }) => (
                <RadioYN
                  name="cove"
                  label="¿Es COVE (Centro de Operación en Vigilancia Epidemiológica)?"
                  value={field.value}
                  onChange={field.onChange}
                />
              )}
            />

            <Controller
              name="unidadAnalisis"
              control={control}
              render={({ field }) => (
                <RadioYN
                  name="unidadAnalisis"
                  label="¿Cuenta con unidad de análisis?"
                  value={field.value}
                  onChange={field.onChange}
                  error={errors.unidadAnalisis?.message}
                />
              )}
            />

            <Controller
              name="internet"
              control={control}
              render={({ field }) => (
                <RadioYN
                  name="internet"
                  label="¿Cuenta con acceso a internet?"
                  value={field.value}
                  onChange={field.onChange}
                />
              )}
            />

            <Controller
              name="activo"
              control={control}
              render={({ field }) => (
                <RadioYN
                  name="activo"
                  label="¿La UPGD está activa?"
                  value={field.value}
                  onChange={field.onChange}
                />
              )}
            />
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Ubicación</h2>
            <div className={styles.grid}>
              <Field
                label="Departamento"
                htmlFor="departamentoCodigo"
                error={errors.departamentoCodigo?.message ?? undefined}
              >
                <Select
                  id="departamentoCodigo"
                  aria-invalid={Boolean(errors.departamentoCodigo)}
                  {...register("departamentoCodigo", {
                    setValueAs: (value) => (value === "" ? null : value),
                  })}
                >
                  <option value="">Seleccione…</option>
                  {DEPARTAMENTOS.map((dep) => (
                    <option key={dep.codigo} value={dep.codigo}>
                      {dep.codigo} — {dep.nombre}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field
                label="Municipio"
                htmlFor="municipioCodigo"
                error={errors.municipioCodigo?.message ?? undefined}
              >
                <Select
                  id="municipioCodigo"
                  aria-invalid={Boolean(errors.municipioCodigo)}
                  {...register("municipioCodigo", {
                    setValueAs: (value) => (value === "" ? null : value),
                  })}
                >
                  <option value="">Seleccione…</option>
                  {MUNICIPIOS.map((mun) => (
                    <option key={mun.codigo} value={mun.codigo}>
                      {mun.codigo} — {mun.nombre}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
          </section>

          {submitError && <p className={styles.errorBanner}>{submitError}</p>}
          {success && (
            <p className={styles.successBanner}>
              UPGD guardada correctamente.
            </p>
          )}

          <button
            type="submit"
            className={styles.submit}
            disabled={isSubmitting}
          >
            {isSubmitting ? "Guardando…" : isEditing ? "Actualizar" : "Guardar"}
          </button>
        </form>
      )}
    </div>
  );
}

export default function CaracterizacionPage() {
  return (
    <Suspense fallback={<p className={styles.loading}>Cargando…</p>}>
      <CaracterizacionForm />
    </Suspense>
  );
}
