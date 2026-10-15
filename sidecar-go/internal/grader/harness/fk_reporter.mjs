// FreeKnowledge node:test reporter. Appends one JSON record per test to
// $FK_RESULTS; it prints nothing, so the terminal shows only program output.
import { appendFileSync } from "node:fs";

const results = process.env.FK_RESULTS;

function message(error) {
  const cause = error?.cause ?? error;
  if (!cause) return "";
  return String(cause.message ?? cause);
}

export default async function* reporter(source) {
  for await (const event of source) {
    if (event.type !== "test:pass" && event.type !== "test:fail") continue;
    const d = event.data;
    if (d.details?.type === "suite") continue;
    const status = d.skip || d.todo ? "skip" : event.type === "test:pass" ? "pass" : "fail";
    const record = {
      name: d.name,
      status,
      message: status === "fail" ? message(d.details?.error) : "",
      durationMs: Math.round(d.details?.duration_ms ?? 0),
    };
    appendFileSync(results, JSON.stringify(record) + "\n");
  }
}
