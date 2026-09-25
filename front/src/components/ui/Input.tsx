import { forwardRef, type InputHTMLAttributes } from "react";
import styles from "./Input.module.scss";

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, ...props },
  ref,
) {
  const classes = [styles.input, className].filter(Boolean).join(" ");
  return <input ref={ref} className={classes} {...props} />;
});
