import { RagForm } from "./rag-form";

export default function RagTestPage() {
  return (
    <div className="space-y-6">
      <p className="rounded-md bg-amber-50 px-4 py-3 text-sm font-semibold text-unclear">Testmodus — nicht produktiv</p>
      <RagForm />
    </div>
  );
}
