import type { ReactNode } from "react";
import styles from "./layout.module.scss";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <span className={styles.brand}>SIVIGILA</span>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}
