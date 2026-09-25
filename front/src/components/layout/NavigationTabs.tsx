"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUserStore } from "@/store/useUserStore";
import styles from "./NavigationTabs.module.scss";

interface Tab {
  href: string;
  label: string;
}

const MIS_ESCENARIOS: Tab = { href: "/mis-escenarios", label: "Mis escenarios" };
const DOCENTE: Tab = { href: "/docente/escenarios", label: "Docente" };

export function NavigationTabs() {
  const pathname = usePathname();
  const rol = useUserStore((state) => state.user?.rol);

  const isDocente = rol === "DOCENTE";
  const tabs = isDocente ? [DOCENTE] : [MIS_ESCENARIOS];

  return (
    <nav className={styles.nav} aria-label="Navegación principal">
      {tabs.map((tab) => {
        const isActive =
          pathname === tab.href || pathname.startsWith(`${tab.href}/`);
        const classes = isActive
          ? `${styles.tab} ${styles.active}`
          : styles.tab;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={classes}
            aria-current={isActive ? "page" : undefined}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
