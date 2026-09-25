"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/axios";
import { Input } from "@/components/ui/Input";
import type { EstadoFicha } from "@/types";
import styles from "./SearchModal.module.scss";

interface SearchResult {
  num_id: string;
  primer_nombre: string;
  primer_apellido: string;
  cod_evento: string;
  estado: EstadoFicha;
}

interface SearchModalProps {
  onClose: () => void;
}

export function SearchModal({ onClose }: SearchModalProps) {
  const router = useRouter();
  const [numId, setNumId] = useState("");
  const [codEvento, setCodEvento] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const handleSearch = async () => {
    const query = numId.trim();
    if (!query) return;

    setLoading(true);
    setError(null);
    setSearched(false);

    try {
      const params: Record<string, string> = { num_id: query };
      if (codEvento.trim()) params.cod_evento = codEvento.trim();

      const { data } = await api.get<SearchResult[]>("/fichas/datos-basicos", {
        params,
      });

      const list = Array.isArray(data) ? data : (data as { data?: SearchResult[] })?.data ?? [];
      setResults(list);
      setSearched(true);
    } catch {
      setError("No se pudo realizar la búsqueda. Intente nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (result: SearchResult) => {
    onClose();
    router.push(`/notificacion/datos-basicos?numId=${encodeURIComponent(result.num_id)}`);
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="search-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className={styles.header}>
          <h2 className={styles.title} id="search-modal-title">
            Buscar casos
          </h2>
          <button
            type="button"
            className={styles.close}
            onClick={onClose}
            aria-label="Cerrar"
          >
            ×
          </button>
        </header>

        <div className={styles.fields}>
          <Input
            autoFocus
            placeholder="Número de identificación"
            value={numId}
            onChange={(event) => setNumId(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") handleSearch();
            }}
          />
          <Input
            placeholder="Código de evento (opcional)"
            value={codEvento}
            onChange={(event) => setCodEvento(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") handleSearch();
            }}
          />
          <button
            type="button"
            className={styles.search}
            onClick={handleSearch}
            disabled={loading || !numId.trim()}
          >
            {loading ? "Buscando…" : "Buscar"}
          </button>
        </div>

        <div className={styles.body}>
          {error && <p className={styles.error}>{error}</p>}

          {!error && searched && results.length === 0 && (
            <p className={styles.empty}>
              No se encontraron casos para los criterios indicados.
            </p>
          )}

          {results.length > 0 && (
            <ul className={styles.list}>
              {results.map((result, index) => (
                <li key={`${result.num_id}-${index}`}>
                  <button
                    type="button"
                    className={styles.result}
                    onClick={() => handleSelect(result)}
                  >
                    <div className={styles.resultMain}>
                      <span className={styles.resultId}>{result.num_id}</span>
                      <span className={styles.resultName}>
                        {result.primer_nombre} {result.primer_apellido}
                      </span>
                    </div>
                    <div className={styles.resultMeta}>
                      <span>Evento {result.cod_evento}</span>
                      <span className={styles.estado}>{result.estado}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
