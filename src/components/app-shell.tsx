"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/hochladen", label: "Rechnung hochladen" },
  { href: "/chat", label: "Chat" },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex gap-1 md:flex-col">
      {NAV.map((punkt) => {
        const aktiv = pathname === punkt.href;
        return (
          <Link
            key={punkt.href}
            href={punkt.href}
            onClick={onNavigate}
            className={`rounded-md px-3 py-2 text-sm ${aktiv ? "bg-navy text-white" : "text-ink/80 hover:bg-paper"}`}
          >
            {punkt.label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [sichtbar, setSichtbar] = useState(false);
  useEffect(() => setSichtbar(true), []);
  if (!sichtbar) return <div className="min-h-screen bg-paper" />;

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-card md:flex">
        <div className="border-b border-line px-5 py-6">
          <Link href="/" className="block">
            <span className="text-xs font-semibold tracking-widest text-navy/70">KSK-ASSISTENT</span>
            <span className="mt-1 block text-lg font-semibold text-navy">Prüfstelle</span>
          </Link>
        </div>
        <div className="flex-1 px-3 py-4">
          <NavLinks />
        </div>
        <p className="border-t border-line px-5 py-4 text-xs leading-relaxed text-ink/70">
          Regeln in Dateien, nicht in schwarzen Boxen. Jede Entscheidung mit Fundstelle.
        </p>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-line bg-card md:hidden">
          <div className="px-4 py-3">
            <Link href="/" className="text-sm font-semibold text-navy">KSK-Prüfstelle</Link>
          </div>
          <div className="flex gap-1 overflow-x-auto px-3 pb-3">
            <NavLinks />
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 md:px-10">{children}</main>
        <footer className="border-t border-line bg-card px-4 py-4 text-xs leading-relaxed text-ink/70 md:px-10">
          <p>Ihre Dokumente werden nicht an Dritte weitergegeben. Die Datei bleibt in diesem Browser.</p>
          <p className="mt-1">Vorschlag, keine Rechts- oder Steuerberatung.</p>
        </footer>
      </div>
    </div>
  );
}
