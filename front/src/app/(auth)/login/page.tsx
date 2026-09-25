"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { useAuth } from "@/hooks/useAuth";
import { ROLES_NO_DOCENTE, type Rol } from "@/types";
import styles from "./login.module.scss";

type Modo = "estudiante" | "docente";
type Vista = "login" | "registro";

const loginSchema = z.discriminatedUnion("modo", [
  z.object({
    modo: z.literal("estudiante"),
    username: z
      .string()
      .min(1, "El email es obligatorio")
      .email("Ingrese un email válido"),
    password: z.string().min(1, "El número de identificación es obligatorio"),
  }),
  z.object({
    modo: z.literal("docente"),
    username: z.string().min(1, "El usuario es obligatorio"),
    password: z.string().min(1, "La contraseña es obligatoria"),
  }),
]);

type LoginFormValues = z.infer<typeof loginSchema>;

const registerSchema = z.object({
  email: z
    .string()
    .min(1, "El email es obligatorio")
    .email("Ingrese un email válido"),
  nombreCompleto: z.string().min(1, "El nombre completo es obligatorio"),
  numeroIdentificacion: z
    .string()
    .min(1, "El número de identificación es obligatorio"),
  rol: z.enum(ROLES_NO_DOCENTE),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

function LoginForm({ onShowRegister }: { onShowRegister: () => void }) {
  const router = useRouter();
  const { login } = useAuth();
  const [modo, setModo] = useState<Modo>("estudiante");
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    clearErrors,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      modo: "estudiante",
      username: "",
      password: "",
    },
  });

  const selectModo = (next: Modo) => {
    setModo(next);
    setError(null);
    clearErrors();
    setValue("modo", next, { shouldValidate: true });
  };

  const onSubmit = async (values: LoginFormValues) => {
    setError(null);
    try {
      await login(values.username, values.password);
      router.replace("/");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError(
          modo === "estudiante"
            ? "Email o número de identificación incorrectos."
            : "Usuario o contraseña incorrectos.",
        );
      } else {
        setError("No se pudo iniciar sesión. Intente nuevamente.");
      }
    }
  };

  const isEstudiante = modo === "estudiante";

  return (
    <>
      <div className={styles.modes} role="tablist" aria-label="Modo de acceso">
        <button
          type="button"
          role="tab"
          aria-selected={isEstudiante}
          className={isEstudiante ? styles.modeActive : styles.mode}
          onClick={() => selectModo("estudiante")}
        >
          Estudiante
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={!isEstudiante}
          className={!isEstudiante ? styles.modeActive : styles.mode}
          onClick={() => selectModo("docente")}
        >
          Docente
        </button>
      </div>

      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        <input type="hidden" {...register("modo")} />

        <label className={styles.field}>
          <span className={styles.label}>
            {isEstudiante ? "Email" : "Usuario"}
          </span>
          <input
            type={isEstudiante ? "email" : "text"}
            className={styles.input}
            autoComplete={isEstudiante ? "email" : "username"}
            {...register("username")}
          />
          {errors.username && (
            <span className={styles.error}>{errors.username.message}</span>
          )}
        </label>

        <label className={styles.field}>
          <span className={styles.label}>
            {isEstudiante ? "Número de identificación" : "Contraseña"}
          </span>
          <input
            type={isEstudiante ? "text" : "password"}
            className={styles.input}
            autoComplete={isEstudiante ? undefined : "current-password"}
            {...register("password")}
          />
          {errors.password && (
            <span className={styles.error}>{errors.password.message}</span>
          )}
        </label>

        {error && <p className={styles.error}>{error}</p>}

        <button
          type="submit"
          className={styles.submit}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Ingresando..." : "Ingresar"}
        </button>
      </form>

      <button
        type="button"
        className={styles.switchLink}
        onClick={onShowRegister}
      >
        Registrarme como estudiante
      </button>
    </>
  );
}

function RegisterForm({ onBack }: { onBack: () => void }) {
  const router = useRouter();
  const { register: registerAccount } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      nombreCompleto: "",
      numeroIdentificacion: "",
      rol: "UPGD",
    },
  });

  const onSubmit = async (values: RegisterFormValues) => {
    setError(null);
    try {
      await registerAccount({
        email: values.email,
        nombreCompleto: values.nombreCompleto,
        numeroIdentificacion: values.numeroIdentificacion,
        rol: values.rol as Rol,
      });
      router.replace("/");
    } catch (err) {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 409) {
          setError("Ya existe un usuario con ese email.");
        } else if (err.response?.status === 422) {
          setError(
            err.response?.data?.detail ??
              "No se pudo completar el registro. Verificá los datos.",
          );
        } else {
          setError("No se pudo completar el registro. Intente nuevamente.");
        }
      } else {
        setError("No se pudo completar el registro. Intente nuevamente.");
      }
    }
  };

  return (
    <>
      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        <label className={styles.field}>
          <span className={styles.label}>Email</span>
          <input
            type="email"
            className={styles.input}
            autoComplete="email"
            {...register("email")}
          />
          {errors.email && (
            <span className={styles.error}>{errors.email.message}</span>
          )}
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Nombre completo</span>
          <input
            type="text"
            className={styles.input}
            autoComplete="name"
            {...register("nombreCompleto")}
          />
          {errors.nombreCompleto && (
            <span className={styles.error}>{errors.nombreCompleto.message}</span>
          )}
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Número de identificación</span>
          <input
            type="text"
            className={styles.input}
            autoComplete="off"
            {...register("numeroIdentificacion")}
          />
          {errors.numeroIdentificacion && (
            <span className={styles.error}>
              {errors.numeroIdentificacion.message}
            </span>
          )}
        </label>

        <label className={styles.field}>
          <span className={styles.label}>Rol</span>
          <select className={styles.select} {...register("rol")}>
            {ROLES_NO_DOCENTE.map((rol) => (
              <option key={rol} value={rol}>
                {rol}
              </option>
            ))}
          </select>
          {errors.rol && (
            <span className={styles.error}>{errors.rol.message}</span>
          )}
        </label>

        {error && <p className={styles.error}>{error}</p>}

        <button
          type="submit"
          className={styles.submit}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Registrando..." : "Registrarme"}
        </button>
      </form>

      <button type="button" className={styles.switchLink} onClick={onBack}>
        Volver al inicio de sesión
      </button>
    </>
  );
}

export default function LoginPage() {
  const [vista, setVista] = useState<Vista>("login");

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>SIVIGILA</h1>
          <p className={styles.subtitle}>
            Simulador educativo de vigilancia en salud pública
          </p>
        </header>

        {vista === "login" ? (
          <LoginForm onShowRegister={() => setVista("registro")} />
        ) : (
          <RegisterForm onBack={() => setVista("login")} />
        )}
      </div>
    </main>
  );
}
