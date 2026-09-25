"use client";

import Link from "next/link";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { FichaViewer } from "@/components/ficha/FichaViewer";
import styles from "./resumen.module.scss";

function ResumenContent() {
  const searchParams = useSearchParams();
  const fichaBasicaIdParam = searchParams.get("ficha_basica_id");
  const parsedId = fichaBasicaIdParam ? Number(fichaBasicaIdParam) : NaN;
  const fichaBasicaId =
    Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Resumen de tu ficha</h1>
        <p className={styles.subtitle}>
          Revisá las respuestas que registraste en el caso.
        </p>
      </header>

      {fichaBasicaId == null ? (
        <p className={styles.errorBanner}>
          No se pudo identificar la ficha a mostrar. Volvé a mis escenarios e
          intentá nuevamente.
        </p>
      ) : (
        <FichaViewer fichaBasicaId={fichaBasicaId} />
      )}

      <div className={styles.actions}>
        <Link href="/mis-escenarios" className={styles.button}>
          Volver a mis escenarios
        </Link>
      </div>
    </div>
  );
}

export default function ResumenPage() {
  return (
    <Suspense fallback={<p className={styles.loading}>Cargando…</p>}>
      <ResumenContent />
    </Suspense>
  );
}
