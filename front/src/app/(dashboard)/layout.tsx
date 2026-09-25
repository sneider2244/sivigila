import type { ReactNode } from "react";
import { Actionbar } from "@/components/layout/Actionbar";
import { AuthGuard } from "@/components/layout/AuthGuard";
import styles from "./layout.module.scss";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <div className={styles.shell}>
        <Actionbar />
        <main className={styles.main}>{children}</main>
      </div>
    </AuthGuard>
  );
}
