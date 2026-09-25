import type { ReactNode } from "react";
import styles from "./Section.module.scss";

interface SectionProps {
  step?: string;
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function Section({ step, title, subtitle, children }: SectionProps) {
  return (
    <section className={styles.card}>
      <header className={styles.head}>
        {step && <span className={styles.badge}>{step}</span>}
        <div className={styles.heading}>
          <h2 className={styles.title}>{title}</h2>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
      </header>
      <div className={styles.body}>{children}</div>
    </section>
  );
}
