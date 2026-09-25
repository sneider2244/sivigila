"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Controller, useForm, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { Field } from "@/components/ui/Field";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RadioYN } from "@/components/ui/RadioYN";
import { useUserStore } from "@/store/useUserStore";
import { createFichaDatosBasicos } from "@/lib/fichas";
import type {
  AreaOcurrencia,
  ClasificacionCaso,
  CondicionFinal,
  FichaDatosBasicos,
  UnidadMedidaEdad,
} from "@/types";
import styles from "./datos-basicos.module.scss";

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

const TIPOS_ID = [
  { codigo: "RC", nombre: "Registro civil" },
  { codigo: "TI", nombre: "Tarjeta de identidad" },
  { codigo: "CC", nombre: "Cédula de ciudadanía" },
  { codigo: "CE", nombre: "Cédula de extranjería" },
  { codigo: "PA", nombre: "Pasaporte" },
  { codigo: "AS", nombre: "Adulto sin identificación" },
  { codigo: "MS", nombre: "Menor sin identificación" },
];

const gruposPoblacionalesSchema = z.object({
  gestante: z.boolean(),
  semanasGestacion: z.number().nullable(),
  desplazado: z.boolean(),
  otraIdentidad: z.string().nullable(),
  fHospitalizacion: z.string().nullable(),
  fDefuncion: z.string().nullable(),
  certificado: z.string().nullable(),
});

const datosBasicosSchema = z
  .object({
    codUpgd: z.string().min(1, "El código UPGD es obligatorio"),
    subindice: z.string(),
    codEvento: z.string().min(1, "El evento es obligatorio"),
    fGrabacion: z.string().min(1, "La fecha de grabación es obligatoria"),
    fNotificacion: z
      .string()
      .min(1, "La fecha de notificación es obligatoria"),
    anio: z.number({ error: "El año es obligatorio" }).int().min(1900).max(2100),
    semanaEpidemiologica: z
      .number({ error: "La semana epidemiológica es obligatoria" })
      .int()
      .min(1)
      .max(53),
    tipoId: z.string().min(1, "El tipo de identificación es obligatorio"),
    numId: z.string().min(1, "El número de identificación es obligatorio"),
    primerNombre: z.string().min(1, "El primer nombre es obligatorio"),
    segundoNombre: z.string(),
    primerApellido: z.string().min(1, "El primer apellido es obligatorio"),
    segundoApellido: z.string(),
    telefono: z.string(),
    fNacimiento: z.string().min(1, "La fecha de nacimiento es obligatoria"),
    edad: z.number({ error: "La edad es obligatoria" }).int().min(0).max(150),
    undMedEdad: z
      .number({ error: "Seleccione la unidad de medida de la edad" })
      .int()
      .min(1)
      .max(3),
    sexo: z.enum(["M", "F"], { error: "Seleccione el sexo" }),
    identidadGenero: z
      .number({ error: "Seleccione la identidad de género" })
      .int()
      .min(1),
    orientacionSexual: z
      .number({ error: "Seleccione la orientación sexual" })
      .int()
      .min(1),
    paisOcurrencia: z.string(),
    dptoOcurrencia: z
      .string()
      .min(1, "El departamento de ocurrencia es obligatorio"),
    muniOcurrencia: z
      .string()
      .min(1, "El municipio de ocurrencia es obligatorio"),
    areaOcurrencia: z
      .number({ error: "Seleccione el área de ocurrencia" })
      .int()
      .min(1)
      .max(3),
    gruposPoblacionales: gruposPoblacionalesSchema,
    clasificacionCaso: z
      .number({ error: "Seleccione la clasificación del caso" })
      .int()
      .min(1)
      .max(4),
    hospitalizado: z.boolean(),
    condicionFinal: z
      .number({ error: "Seleccione la condición final" })
      .int()
      .min(1)
      .max(2),
  })
  .superRefine((data, ctx) => {
    const gp = data.gruposPoblacionales;

    if (data.identidadGenero === 5 && !gp.otraIdentidad?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["gruposPoblacionales", "otraIdentidad"],
        message: "Indique cuál es su identidad de género",
      });
    }

    if (gp.gestante && gp.semanasGestacion == null) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["gruposPoblacionales", "semanasGestacion"],
        message: "Indique las semanas de gestación",
      });
    }

    if (data.hospitalizado && !gp.fHospitalizacion) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["gruposPoblacionales", "fHospitalizacion"],
        message: "Indique la fecha de hospitalización",
      });
    }

    if (data.condicionFinal === 2 && !gp.fDefuncion) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["gruposPoblacionales", "fDefuncion"],
        message: "Indique la fecha de defunción",
      });
    }

    if (data.condicionFinal === 2 && !gp.certificado?.trim()) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["gruposPoblacionales", "certificado"],
        message: "Indique el número del certificado de defunción",
      });
    }
  });

type DatosBasicosFormValues = z.infer<typeof datosBasicosSchema>;

const currentYear = new Date().getFullYear();

function DatosBasicosForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const asignacionIdParam = searchParams.get("asignacion_id");
  const codEventoParam = searchParams.get("cod_evento");
  const asignacionId = asignacionIdParam ? Number(asignacionIdParam) : null;
  const esEntrega =
    asignacionId != null && Number.isInteger(asignacionId) && asignacionId > 0;

  const user = useUserStore((state) => state.user);

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DatosBasicosFormValues>({
    resolver: zodResolver(datosBasicosSchema),
    defaultValues: {
      codUpgd: user?.codUpgd ?? "",
      subindice: "01",
      codEvento: codEventoParam ?? "",
      fGrabacion: "",
      fNotificacion: "",
      anio: currentYear,
      semanaEpidemiologica: undefined,
      tipoId: "CC",
      numId: "",
      primerNombre: "",
      segundoNombre: "",
      primerApellido: "",
      segundoApellido: "",
      telefono: "",
      fNacimiento: "",
      edad: undefined,
      undMedEdad: 1,
      sexo: "M",
      identidadGenero: 1,
      orientacionSexual: 1,
      paisOcurrencia: "COLOMBIA",
      dptoOcurrencia: "",
      muniOcurrencia: "",
      areaOcurrencia: 1,
      gruposPoblacionales: {
        gestante: false,
        semanasGestacion: null,
        desplazado: false,
        otraIdentidad: null,
        fHospitalizacion: null,
        fDefuncion: null,
        certificado: null,
      },
      clasificacionCaso: 1,
      hospitalizado: false,
      condicionFinal: 1,
    },
  });

  const identidadGenero = useWatch({ control, name: "identidadGenero" });
  const gestante = useWatch({ control, name: "gruposPoblacionales.gestante" });
  const hospitalizado = useWatch({ control, name: "hospitalizado" });
  const condicionFinal = useWatch({ control, name: "condicionFinal" });

  const onSubmit = async (values: DatosBasicosFormValues) => {
    setSubmitError(null);
    setSuccess(false);

    const ficha: FichaDatosBasicos = {
      codUpgd: values.codUpgd,
      subindice: values.subindice,
      codEvento: values.codEvento,
      fGrabacion: values.fGrabacion,
      fNotificacion: values.fNotificacion,
      anio: values.anio,
      semanaEpidemiologica: values.semanaEpidemiologica,
      tipoId: values.tipoId,
      numId: values.numId,
      primerNombre: values.primerNombre,
      segundoNombre: values.segundoNombre.trim() || null,
      primerApellido: values.primerApellido,
      segundoApellido: values.segundoApellido.trim() || null,
      telefono: values.telefono.trim() || null,
      fNacimiento: values.fNacimiento,
      edad: values.edad,
      undMedEdad: values.undMedEdad as UnidadMedidaEdad,
      sexo: values.sexo,
      identidadGenero: values.identidadGenero,
      orientacionSexual: values.orientacionSexual,
      paisOcurrencia: values.paisOcurrencia,
      dptoOcurrencia: values.dptoOcurrencia,
      muniOcurrencia: values.muniOcurrencia,
      areaOcurrencia: values.areaOcurrencia as AreaOcurrencia,
      gruposPoblacionales: {
        gestante: values.gruposPoblacionales.gestante,
        semanasGestacion: values.gruposPoblacionales.semanasGestacion,
        desplazado: values.gruposPoblacionales.desplazado,
        otraIdentidad: values.gruposPoblacionales.otraIdentidad?.trim() || null,
        fHospitalizacion: values.gruposPoblacionales.fHospitalizacion,
        fDefuncion: values.gruposPoblacionales.fDefuncion,
        certificado: values.gruposPoblacionales.certificado?.trim() || null,
      },
      clasificacionCaso: values.clasificacionCaso as ClasificacionCaso,
      hospitalizado: values.hospitalizado,
      condicionFinal: values.condicionFinal as CondicionFinal,
      estado: "NOTIFICADA",
    };

    try {
      const fichaCreada = await createFichaDatosBasicos(ficha);
      if (esEntrega && asignacionId != null) {
        const params = new URLSearchParams({
          asignacion_id: String(asignacionId),
          ficha_basica_id: String(fichaCreada.id),
          cod_evento: values.codEvento,
        });
        router.replace(
          `/notificacion/datos-complementarios?${params.toString()}`,
        );
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
        <h1 className={styles.title}>Datos Básicos</h1>
        <p className={styles.subtitle}>
          Notificación individual de caso en salud pública.
        </p>
      </header>

      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Identificación de la ficha</h2>
          <div className={styles.grid}>
            <Field
              label="Código UPGD"
              htmlFor="codUpgd"
              error={errors.codUpgd?.message}
            >
              <Input
                id="codUpgd"
                aria-invalid={Boolean(errors.codUpgd)}
                placeholder="12 caracteres"
                {...register("codUpgd")}
              />
            </Field>
            <Field
              label="Evento"
              htmlFor="codEvento"
              error={errors.codEvento?.message}
            >
              <Input
                id="codEvento"
                aria-invalid={Boolean(errors.codEvento)}
                placeholder="Código del evento"
                {...register("codEvento")}
              />
            </Field>
            <Field
              label="Fecha de grabación"
              htmlFor="fGrabacion"
              error={errors.fGrabacion?.message}
            >
              <Input
                id="fGrabacion"
                type="date"
                aria-invalid={Boolean(errors.fGrabacion)}
                {...register("fGrabacion")}
              />
            </Field>
            <Field
              label="Fecha de notificación"
              htmlFor="fNotificacion"
              error={errors.fNotificacion?.message}
            >
              <Input
                id="fNotificacion"
                type="date"
                aria-invalid={Boolean(errors.fNotificacion)}
                {...register("fNotificacion")}
              />
            </Field>
            <Field label="Año" htmlFor="anio" error={errors.anio?.message}>
              <Input
                id="anio"
                type="number"
                aria-invalid={Boolean(errors.anio)}
                {...register("anio", {
                  setValueAs: (value) => (value === "" ? undefined : Number(value)),
                })}
              />
            </Field>
            <Field
              label="Semana epidemiológica"
              htmlFor="semanaEpidemiologica"
              error={errors.semanaEpidemiologica?.message}
            >
              <Input
                id="semanaEpidemiologica"
                type="number"
                aria-invalid={Boolean(errors.semanaEpidemiologica)}
                {...register("semanaEpidemiologica", {
                  setValueAs: (value) => (value === "" ? undefined : Number(value)),
                })}
              />
            </Field>
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Identificación del paciente</h2>
          <div className={styles.grid}>
            <Field
              label="Tipo de identificación"
              htmlFor="tipoId"
              error={errors.tipoId?.message}
            >
              <Select
                id="tipoId"
                aria-invalid={Boolean(errors.tipoId)}
                {...register("tipoId")}
              >
                {TIPOS_ID.map((t) => (
                  <option key={t.codigo} value={t.codigo}>
                    {t.codigo} — {t.nombre}
                  </option>
                ))}
              </Select>
            </Field>
            <Field
              label="Número de identificación"
              htmlFor="numId"
              error={errors.numId?.message}
            >
              <Input
                id="numId"
                aria-invalid={Boolean(errors.numId)}
                placeholder="Número de documento"
                {...register("numId")}
              />
            </Field>
            <Field
              label="Primer nombre"
              htmlFor="primerNombre"
              error={errors.primerNombre?.message}
            >
              <Input
                id="primerNombre"
                aria-invalid={Boolean(errors.primerNombre)}
                {...register("primerNombre")}
              />
            </Field>
            <Field label="Segundo nombre" htmlFor="segundoNombre">
              <Input id="segundoNombre" {...register("segundoNombre")} />
            </Field>
            <Field
              label="Primer apellido"
              htmlFor="primerApellido"
              error={errors.primerApellido?.message}
            >
              <Input
                id="primerApellido"
                aria-invalid={Boolean(errors.primerApellido)}
                {...register("primerApellido")}
              />
            </Field>
            <Field label="Segundo apellido" htmlFor="segundoApellido">
              <Input id="segundoApellido" {...register("segundoApellido")} />
            </Field>
            <Field label="Teléfono" htmlFor="telefono">
              <Input id="telefono" placeholder="Opcional" {...register("telefono")} />
            </Field>
            <Field
              label="Fecha de nacimiento"
              htmlFor="fNacimiento"
              error={errors.fNacimiento?.message}
            >
              <Input
                id="fNacimiento"
                type="date"
                aria-invalid={Boolean(errors.fNacimiento)}
                {...register("fNacimiento")}
              />
            </Field>
            <Field label="Edad" htmlFor="edad" error={errors.edad?.message}>
              <Input
                id="edad"
                type="number"
                aria-invalid={Boolean(errors.edad)}
                {...register("edad", {
                  setValueAs: (value) => (value === "" ? undefined : Number(value)),
                })}
              />
            </Field>
            <Field
              label="Unidad de medida de la edad"
              htmlFor="undMedEdad"
              error={errors.undMedEdad?.message}
            >
              <Select
                id="undMedEdad"
                aria-invalid={Boolean(errors.undMedEdad)}
                {...register("undMedEdad", {
                  setValueAs: (value) => (value === "" ? undefined : Number(value)),
                })}
              >
                <option value="1">Años</option>
                <option value="2">Meses</option>
                <option value="3">Días</option>
              </Select>
            </Field>
            <Field label="Sexo" htmlFor="sexo" error={errors.sexo?.message}>
              <Select
                id="sexo"
                aria-invalid={Boolean(errors.sexo)}
                {...register("sexo")}
              >
                <option value="M">Masculino</option>
                <option value="F">Femenino</option>
              </Select>
            </Field>
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Identidad y orientación</h2>
          <div className={styles.grid}>
            <Field
              label="Identidad de género"
              htmlFor="identidadGenero"
              error={errors.identidadGenero?.message}
            >
              <Select
                id="identidadGenero"
                aria-invalid={Boolean(errors.identidadGenero)}
                {...register("identidadGenero", {
                  setValueAs: (value) => (value === "" ? undefined : Number(value)),
                })}
              >
                <option value="1">Mujer</option>
                <option value="2">Hombre</option>
                <option value="3">Transgénero</option>
                <option value="4">No binario</option>
                <option value="5">Otro</option>
              </Select>
            </Field>
            <Field
              label="Orientación sexual"
              htmlFor="orientacionSexual"
              error={errors.orientacionSexual?.message}
            >
              <Select
                id="orientacionSexual"
                aria-invalid={Boolean(errors.orientacionSexual)}
                {...register("orientacionSexual", {
                  setValueAs: (value) => (value === "" ? undefined : Number(value)),
                })}
              >
                <option value="1">Heterosexual</option>
                <option value="2">Homosexual</option>
                <option value="3">Bisexual</option>
                <option value="4">Otro</option>
              </Select>
            </Field>
          </div>

          {identidadGenero === 5 && (
            <div className={styles.conditional}>
              <Field
                label="¿Cuál identidad de género?"
                htmlFor="gruposPoblacionales.otraIdentidad"
                error={errors.gruposPoblacionales?.otraIdentidad?.message}
              >
                <Input
                  id="gruposPoblacionales.otraIdentidad"
                  aria-invalid={Boolean(errors.gruposPoblacionales?.otraIdentidad)}
                  {...register("gruposPoblacionales.otraIdentidad", {
                    setValueAs: (value) => (value === "" ? null : value),
                  })}
                />
              </Field>
            </div>
          )}
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Ubicación de ocurrencia</h2>
          <div className={styles.grid}>
            <Field label="País" htmlFor="paisOcurrencia">
              <Input id="paisOcurrencia" {...register("paisOcurrencia")} />
            </Field>
            <Field
              label="Departamento"
              htmlFor="dptoOcurrencia"
              error={errors.dptoOcurrencia?.message}
            >
              <Select
                id="dptoOcurrencia"
                aria-invalid={Boolean(errors.dptoOcurrencia)}
                {...register("dptoOcurrencia")}
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
              htmlFor="muniOcurrencia"
              error={errors.muniOcurrencia?.message}
            >
              <Select
                id="muniOcurrencia"
                aria-invalid={Boolean(errors.muniOcurrencia)}
                {...register("muniOcurrencia")}
              >
                <option value="">Seleccione…</option>
                {MUNICIPIOS.map((mun) => (
                  <option key={mun.codigo} value={mun.codigo}>
                    {mun.codigo} — {mun.nombre}
                  </option>
                ))}
              </Select>
            </Field>
            <Field
              label="Área de ocurrencia"
              htmlFor="areaOcurrencia"
              error={errors.areaOcurrencia?.message}
            >
              <Select
                id="areaOcurrencia"
                aria-invalid={Boolean(errors.areaOcurrencia)}
                {...register("areaOcurrencia", {
                  setValueAs: (value) => (value === "" ? undefined : Number(value)),
                })}
              >
                <option value="1">Cabecera municipal</option>
                <option value="2">Centro poblado</option>
                <option value="3">Rural disperso</option>
              </Select>
            </Field>
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Grupos poblacionales</h2>
          <Controller
            name="gruposPoblacionales.gestante"
            control={control}
            render={({ field }) => (
              <RadioYN
                name="gruposPoblacionales.gestante"
                label="¿La persona se encuentra en estado de gestación?"
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          {gestante && (
            <div className={styles.conditional}>
              <Field
                label="Semanas de gestación"
                htmlFor="gruposPoblacionales.semanasGestacion"
                error={errors.gruposPoblacionales?.semanasGestacion?.message}
              >
                <Input
                  id="gruposPoblacionales.semanasGestacion"
                  type="number"
                  aria-invalid={Boolean(
                    errors.gruposPoblacionales?.semanasGestacion,
                  )}
                  {...register("gruposPoblacionales.semanasGestacion", {
                    setValueAs: (value) => (value === "" ? null : Number(value)),
                  })}
                />
              </Field>
            </div>
          )}
          <Controller
            name="gruposPoblacionales.desplazado"
            control={control}
            render={({ field }) => (
              <RadioYN
                name="gruposPoblacionales.desplazado"
                label="¿La persona se encuentra en situación de desplazamiento?"
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Datos clínicos</h2>
          <Field
            label="Clasificación del caso"
            htmlFor="clasificacionCaso"
            error={errors.clasificacionCaso?.message}
          >
            <Select
              id="clasificacionCaso"
              aria-invalid={Boolean(errors.clasificacionCaso)}
              {...register("clasificacionCaso", {
                setValueAs: (value) => (value === "" ? undefined : Number(value)),
              })}
            >
              <option value="1">Sospechoso</option>
              <option value="2">Probable</option>
              <option value="3">Confirmado</option>
              <option value="4">Descartado</option>
            </Select>
          </Field>

          <Controller
            name="hospitalizado"
            control={control}
            render={({ field }) => (
              <RadioYN
                name="hospitalizado"
                label="¿El paciente fue hospitalizado?"
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          {hospitalizado && (
            <div className={styles.conditional}>
              <Field
                label="Fecha de hospitalización"
                htmlFor="gruposPoblacionales.fHospitalizacion"
                error={errors.gruposPoblacionales?.fHospitalizacion?.message}
              >
                <Input
                  id="gruposPoblacionales.fHospitalizacion"
                  type="date"
                  aria-invalid={Boolean(
                    errors.gruposPoblacionales?.fHospitalizacion,
                  )}
                  {...register("gruposPoblacionales.fHospitalizacion", {
                    setValueAs: (value) => (value === "" ? null : value),
                  })}
                />
              </Field>
            </div>
          )}

          <Field
            label="Condición final"
            htmlFor="condicionFinal"
            error={errors.condicionFinal?.message}
          >
            <Select
              id="condicionFinal"
              aria-invalid={Boolean(errors.condicionFinal)}
              {...register("condicionFinal", {
                setValueAs: (value) => (value === "" ? undefined : Number(value)),
              })}
            >
              <option value="1">Vivo</option>
              <option value="2">Muerto</option>
            </Select>
          </Field>

          {condicionFinal === 2 && (
            <div className={styles.conditional}>
              <div className={styles.grid}>
                <Field
                  label="Fecha de defunción"
                  htmlFor="gruposPoblacionales.fDefuncion"
                  error={errors.gruposPoblacionales?.fDefuncion?.message}
                >
                  <Input
                    id="gruposPoblacionales.fDefuncion"
                    type="date"
                    aria-invalid={Boolean(
                      errors.gruposPoblacionales?.fDefuncion,
                    )}
                    {...register("gruposPoblacionales.fDefuncion", {
                      setValueAs: (value) => (value === "" ? null : value),
                    })}
                  />
                </Field>
                <Field
                  label="Número de certificado de defunción"
                  htmlFor="gruposPoblacionales.certificado"
                  error={errors.gruposPoblacionales?.certificado?.message}
                >
                  <Input
                    id="gruposPoblacionales.certificado"
                    aria-invalid={Boolean(
                      errors.gruposPoblacionales?.certificado,
                    )}
                    {...register("gruposPoblacionales.certificado", {
                      setValueAs: (value) => (value === "" ? null : value),
                    })}
                  />
                </Field>
              </div>
            </div>
          )}
        </section>

        {submitError && <p className={styles.errorBanner}>{submitError}</p>}
        {success && (
          <p className={styles.successBanner}>
            Ficha de datos básicos guardada correctamente.
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

export default function DatosBasicosPage() {
  return (
    <Suspense fallback={<p className={styles.subtitle}>Cargando…</p>}>
      <DatosBasicosForm />
    </Suspense>
  );
}
