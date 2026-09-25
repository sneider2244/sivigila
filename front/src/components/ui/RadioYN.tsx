import styles from "./RadioYN.module.scss";

interface RadioYNProps {
  name: string;
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
  hint?: string;
  error?: string;
}

export function RadioYN({
  name,
  label,
  value,
  onChange,
  hint,
  error,
}: RadioYNProps) {
  return (
    <div className={styles.recurso}>
      <p className={styles.label}>{label}</p>
      <div className={styles.yn}>
        <label className={styles.chip}>
          <input
            type="radio"
            name={name}
            checked={value === true}
            onChange={() => onChange(true)}
          />
          <span>Sí</span>
        </label>
        <label className={styles.chip}>
          <input
            type="radio"
            name={name}
            checked={value === false}
            onChange={() => onChange(false)}
          />
          <span>No</span>
        </label>
      </div>
      {hint && <span className={styles.hint}>{hint}</span>}
      {error && <span className={styles.error}>{error}</span>}
    </div>
  );
}
