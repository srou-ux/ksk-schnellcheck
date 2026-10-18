import { claimNextJob, finishJob } from "../db";
import { captureError } from "../errors";
import { runSaasKiKernel } from "../saas-ki-kernel";

let chain: Promise<void> = Promise.resolve();

export function kickQueue(): Promise<void> {
  chain = chain.then(() => drain()).catch((error) => captureError("queue", error));
  return chain;
}

async function drain(): Promise<void> {
  for (;;) {
    const job = claimNextJob();
    if (!job) return;
    try {
      await runSaasKiKernel({ auftrag: "fall", runId: job.runId });
      finishJob(job.id, null);
    } catch (error) {
      captureError("job", error);
      finishJob(job.id, error instanceof Error ? error.message : "fehlgeschlagen");
    }
  }
}
