"use client";

import { useQuery } from "@tanstack/react-query";
import { getMiEscenario } from "@/lib/estudiante";
import styles from "./CaseBanner.module.scss";

export function CaseBanner({ asignacionId }: { asignacionId: number }) {
  const { data } = useQuery({
    queryKey: ["estudiante", "escenario", asignacionId],
    queryFn: () => getMiEscenario(asignacionId),
    enabled: Number.isInteger(asignacionId) && asignacionId > 0,
  });

  if (!data) {
    return null;
  }

  return (
    <div className={styles.banner} role="note">
      <p className={styles.caseTitle}>Caso: {data.escenario.titulo}</p>
      <p className={styles.caseDesc}>{data.escenario.descripcion}</p>
    </div>
  );
}
