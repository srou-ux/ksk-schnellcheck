import { captureError } from "@/lib/errors";
import { claimVorbereitungsJob, finishVorbereitungsJob, fuehreVorbereitungAus } from "@/lib/jahrespaket-vorbereitung";

let chain: Promise<void> = Promise.resolve();

export function kickVorbereitungsQueue(): Promise<void> {
  chain = chain.then(drain).catch((error) => captureError("jahrespaket-vorbereitung-queue", error));
  return chain;
}

async function drain(): Promise<void> {
  for (;;) {
    const job = claimVorbereitungsJob();
    if (!job) return;
    try {
      await fuehreVorbereitungAus(job.preparationId);
      finishVorbereitungsJob(job.jobId, null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Vorbereitung fehlgeschlagen";
      captureError("jahrespaket-vorbereitung", error);
      finishVorbereitungsJob(job.jobId, message);
    }
  }
}
