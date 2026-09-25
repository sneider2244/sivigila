"use client";

import Link from "next/link";
import { useUserStore } from "@/store/useUserStore";
import styles from "./page.module.scss";

interface ModuleCard {
  href: string;
  title: string;
  description: string;
}

const MIS_ESCENARIOS: ModuleCard = {
  href: "/mis-escenarios",
  title: "Mis escenarios",
  description: "Escenarios clínicos asignados para diligenciar la ficha.",
};

const GESTION_DOCENTE: ModuleCard = {
  href: "/docente/escenarios",
  title: "Gestión docente",
  description: "Crear escenarios clínicos y asignarlos a los estudiantes.",
};

export default function HomePage() {
  const user = useUserStore((state) => state.user);
  const isDocente = user?.rol === "DOCENTE";

  const cards = isDocente ? [GESTION_DOCENTE] : [MIS_ESCENARIOS];

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Hola, {user?.nombreCompleto ?? "usuario"}</h1>
        {user && <p className={styles.subtitle}>Rol actual: {user.rol}</p>}
      </header>

      <section className={styles.grid} aria-label="Módulos disponibles">
        {cards.map((card) => (
          <Link key={card.href} href={card.href} className={styles.card}>
            <h2 className={styles.cardTitle}>{card.title}</h2>
            <p className={styles.cardDescription}>{card.description}</p>
          </Link>
        ))}
      </section>
    </div>
  );
}
