import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppShell } from "@/components/app-shell";
import { PruefProvider } from "@/components/pruef-provider";
import "./globals.css";

const sans = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "KSK-Prüfstelle",
  description: "Vorschlag zur Künstlersozialabgabe. Sie bestätigen jede offene Position.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className={`${sans.variable} min-h-screen antialiased`}>
        <PruefProvider>
          <AppShell>{children}</AppShell>
        </PruefProvider>
      </body>
    </html>
  );
}
