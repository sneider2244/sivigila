import type { Metadata } from "next";
import "@/styles/main.scss";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "SIVIGILA",
  description:
    "Simulador educativo del Sistema de Vigilancia en Salud Pública de Colombia",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
