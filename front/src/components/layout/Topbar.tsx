"use client";

import { useState, type ChangeEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useUserStore } from "@/store/useUserStore";
import { SearchModal } from "@/components/ui/SearchModal";
import { ROLES_NO_DOCENTE, type Rol } from "@/types";
import styles from "./Topbar.module.scss";

export function Topbar() {
  const router = useRouter();
  const user = useUserStore((state) => state.user);
  const { logout, changeRol } = useAuth();
  const [searchOpen, setSearchOpen] = useState(false);
  const [changingRol, setChangingRol] = useState(false);
  const [rolError, setRolError] = useState<string | null>(null);

  const isDocente = user?.rol === "DOCENTE";

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  const handleRolChange = async (event: ChangeEvent<HTMLSelectElement>) => {
    const nuevoRol = event.target.value as Rol;
    if (!user || nuevoRol === user.rol) return;

    setChangingRol(true);
    setRolError(null);
    try {
      await changeRol(nuevoRol);
    } catch {
      setRolError("No se pudo cambiar el rol.");
    } finally {
      setChangingRol(false);
    }
  };

  return (
    <div className={styles.topbar}>
      <span className={styles.brand}>Simulador SIVIGILA</span>

      <div className={styles.user}>
        <span className={styles.name}>{user?.nombreCompleto ?? "—"}</span>
        {user && !isDocente && (
          <div className={styles.rolRow}>
            {/* <select
              className={styles.rolSelect}
              value={user.rol}
              onChange={handleRolChange}
              disabled={changingRol}
              aria-label="Cambiar rol"
            >
              {ROLES_NO_DOCENTE.map((rol) => (
                <option key={rol} value={rol}>
                  {rol}
                </option>
              ))}
            </select> */}
            {user.codUpgd ? (
              <span className={styles.meta}>· {user.codUpgd}</span>
            ) : null}
          </div>
        )}
        {user && isDocente && (
          <span className={styles.meta}>
            {user.rol}
            {user.codUpgd ? ` · ${user.codUpgd}` : ""}
          </span>
        )}
        {rolError && <span className={styles.rolError}>{rolError}</span>}
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.button}
          onClick={handleLogout}
        >
          Cerrar sesión
        </button>
      </div>

      {searchOpen && <SearchModal onClose={() => setSearchOpen(false)} />}
    </div>
  );
}
