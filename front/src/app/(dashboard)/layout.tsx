import type { ReactNode } from "react";
import { Actionbar } from "@/components/layout/Actionbar";
import styles from "./layout.module.scss";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className={styles.shell}>
      <Actionbar />
      <main className={styles.main}>{children}</main>
    </div>
  );
}
