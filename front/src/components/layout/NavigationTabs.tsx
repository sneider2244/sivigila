"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./NavigationTabs.module.scss";

const TABS = [
  { href: "/caracterizacion", label: "Caracterización" },
  { href: "/notificacion/datos-basicos", label: "Datos Básicos" },
  {
    href: "/notificacion/datos-complementarios",
    label: "Datos Complementarios",
  },
];

export function NavigationTabs() {
  const pathname = usePathname();

  return (
    <nav className={styles.nav} aria-label="Navegación principal">
      {TABS.map((tab) => {
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
