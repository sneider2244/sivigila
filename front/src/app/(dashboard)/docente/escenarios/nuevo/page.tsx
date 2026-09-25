"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
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
import { createEscenario } from "@/lib/docente";
import { getEventos } from "@/lib/catalogos";
import styles from "./nuevo.module.scss";

const escenarioSchema = z.object({
  titulo: z.string().min(3, "El título debe tener al menos 3 caracteres"),
  descripcion: z
    .string()
    .min(3, "La descripción debe tener al menos 3 caracteres"),
  codEvento: z.string().min(1, "El código de evento es obligatorio"),
  activo: z.boolean(),
});

type EscenarioFormValues = z.infer<typeof escenarioSchema>;

export default function NuevoEscenarioPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useUserStore((state) => state.user);
  const isDocente = user?.rol === "DOCENTE";
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { data: eventos = [] } = useQuery({
    queryKey: ["catalogos", "eventos"],
    queryFn: getEventos,
    enabled: isDocente,
  });

  const {
    register,
    control,
    handleSubmit,
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
    onSuccess: (creado) => {
      queryClient.invalidateQueries({ queryKey: ["docente", "escenarios"] });
      router.replace(`/docente/escenarios/${creado.id}`);
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
        <h1 className={styles.title}>Crear escenario</h1>
        <p className={styles.subtitle}>
          Definí el caso clínico que resolverán los estudiantes.
        </p>
      </header>

      <div className={styles.actions}>
        <Link href="/docente/escenarios" className={styles.buttonGhost}>
          Volver
        </Link>
      </div>

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
        <button
          type="submit"
          className={styles.submit}
          disabled={isSubmitting || createMutation.isPending}
        >
          {createMutation.isPending ? "Creando…" : "Crear escenario"}
        </button>
      </form>
    </div>
  );
}
