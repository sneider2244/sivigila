import type { Metadata } from "next";
import "@/styles/main.scss";

export const metadata: Metadata = {
  title: "SIVIGILA",
  description:
    "Simulador educativo del Sistema de Vigilancia en Salud Pública de Colombia",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
