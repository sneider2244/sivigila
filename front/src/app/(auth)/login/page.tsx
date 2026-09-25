"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { useAuth } from "@/hooks/useAuth";
import styles from "./login.module.scss";

const loginSchema = z.object({
  username: z.string().min(1, "El usuario es obligatorio"),
  password: z.string().min(6, "La contraseña debe tener al menos 6 caracteres"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (values: LoginFormValues) => {
    setError(null);
    try {
      await login(values.username, values.password);
      router.replace("/");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError("Usuario o contraseña incorrectos.");
      } else {
        setError("No se pudo iniciar sesión. Intente nuevamente.");
      }
    }
  };

  return (
    <main className={styles.page}>
      <div className={styles.card}>
        <header className={styles.header}>
          <h1 className={styles.title}>SIVIGILA</h1>
          <p className={styles.subtitle}>
            Simulador educativo de vigilancia en salud pública
          </p>
        </header>

        <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
          <label className={styles.field}>
            <span className={styles.label}>Usuario</span>
            <input
              type="text"
              className={styles.input}
              autoComplete="username"
              {...register("username")}
            />
            {errors.username && (
              <span className={styles.error}>{errors.username.message}</span>
            )}
          </label>

          <label className={styles.field}>
            <span className={styles.label}>Contraseña</span>
            <input
              type="password"
              className={styles.input}
              autoComplete="current-password"
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
      </div>
    </main>
  );
}
