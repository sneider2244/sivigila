"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useUserStore } from "@/store/useUserStore";
import { SearchModal } from "@/components/ui/SearchModal";
import styles from "./Topbar.module.scss";

export function Topbar() {
  const router = useRouter();
  const user = useUserStore((state) => state.user);
  const { logout } = useAuth();
  const [searchOpen, setSearchOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <div className={styles.topbar}>
      <span className={styles.brand}>SIVIGILA</span>

      <div className={styles.user}>
        <span className={styles.name}>{user?.nombreCompleto ?? "—"}</span>
        {user && (
          <span className={styles.meta}>
            {user.rol}
            {user.codUpgd ? ` · ${user.codUpgd}` : ""}
          </span>
        )}
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.button}
          onClick={() => setSearchOpen(true)}
        >
          Buscar casos
        </button>
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
