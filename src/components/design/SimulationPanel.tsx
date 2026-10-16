import type { SimEvent, SimResult, SimulationConfig } from "../../lib/engine";

interface Props {
  result?: SimResult;
  running: boolean;
  error?: string;
  maxLatencyMs?: number;
  /** The diagram changed after this result was produced. */
  stale?: boolean;
  onNext?: () => void;
  /** Jumps the replay to an event. */
  onSeek?: (ms: number) => void;
  scenario?: SimulationConfig;
}

export function SimulationPanel({ result, running, error, maxLatencyMs, stale, onNext, onSeek, scenario }: Props) {
  const fencing = scenario?.kind === "fencing";
  const requests = scenario?.traffic?.requests ?? 1000;
  return (
    <div className="flex h-full flex-col bg-zinc-950">
      <div className="flex shrink-0 items-center border-b border-zinc-800 px-3 py-2 text-xs">
        <span className="font-medium text-zinc-200">Simulation</span>
        <span className="ml-auto text-zinc-500">
          {running ? (fencing ? "Running the workers…" : "Sending traffic…") : maxLatencyMs ? `Goal: p99 ≤ ${maxLatencyMs} ms` : ""}
        </span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-3 text-sm">
        {error && <p className="text-red-400">{error}</p>}
        {!result && !error && !running && (
          <p className="text-zinc-500">
            Click <span className="text-zinc-300">{fencing ? "Run Scenario" : "Simulate Traffic"}</span> (or press{" "}
            <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs">⌘ Enter</kbd>){" "}
            {fencing ? "to run the workers through the scenario's faults." : `to send ${requests.toLocaleString()} requests through your design.`}
          </p>
        )}
        {result && stale && !running && (
          <p className="mb-3 text-xs text-zinc-500">You've changed the diagram since this run. Simulate again to see how it performs.</p>
        )}
        {result && <Summary result={result} fencing={fencing} onNext={result.experiment ? undefined : onNext} onSeek={onSeek} />}
      </div>
    </div>
  );
}

const EVENT_ICONS: Record<SimEvent["kind"], string> = {
  crash: "⚡",
  partition: "✂",
  failover: "↻",
  bottleneck: "▲",
  queueing: "≡",
  errors: "✗",
  data_loss: "⚠",
  stale: "◷",
  throttled: "⛔",
  deploy: "⇪",
  lock: "🔒",
};

const LOADED = ["server", "database", "cache", "replica", "searchIndex"];

function Summary({ result, fencing, onNext, onSeek }: { result: SimResult; fencing: boolean; onNext?: () => void; onSeek?: (ms: number) => void }) {
  const m = result.metrics;
  const overTarget = m.maxLatencyMs !== undefined && m.p99Ms > m.maxLatencyMs;
  const servers = Object.entries(result.nodes)
    .filter(([, s]) => LOADED.includes(s.type) && !fencing)
    .sort(([, a], [, b]) => b.utilization - a.utilization);

  const cost = result.cost;
  return (
    <div className="space-y-4">
      {result.experiment && (
        <p className="rounded border border-red-900/70 bg-red-950/30 px-3 py-2 text-xs text-red-200">
          ⚡ Chaos experiment: the parts you picked fail 30% of the way into the run. Experiments don't count toward completing the lesson.
        </p>
      )}
      {result.passed ? (
        <div className="flex items-center justify-between gap-3 rounded border border-emerald-800 bg-emerald-950/50 px-3 py-2">
          <span className="font-medium text-emerald-300">{result.message}</span>
          {onNext && (
            <button onClick={onNext} className="shrink-0 rounded bg-emerald-600 px-3 py-1 text-sm font-medium hover:bg-emerald-500">
              Next lesson →
            </button>
          )}
        </div>
      ) : (
        <ul className="space-y-1.5">
          {result.issues.map((i) => (
            <li key={i.code + (i.nodeId ?? "")} className="flex gap-2 rounded border border-red-900/70 bg-red-950/40 px-3 py-2 text-red-200">
              <span className="font-bold text-red-400">✗</span>
              {i.message}
            </li>
          ))}
        </ul>
      )}

      {m.completed > 0 && !fencing && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Metric label="p50 latency" value={`${m.p50Ms} ms`} />
          <Metric label="p99 latency" value={`${m.p99Ms} ms`} bad={overTarget} />
          <Metric label="throughput" value={`${m.throughputPerSec.toLocaleString()}/s`} />
          <Metric label="answered" value={`${m.completed.toLocaleString()} / ${m.requests.toLocaleString()}`} bad={m.failed > 0} />
        </div>
      )}

      {result.stats?.length > 0 && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 rounded border border-zinc-800 bg-zinc-900/40 px-3 py-2 text-xs">
          {result.stats.map((s) => (
            <div key={s.label} className="contents">
              <dt className="text-zinc-400">{s.label}</dt>
              <dd className={`font-mono ${s.status === "bad" ? "text-red-400" : s.status === "good" ? "text-emerald-400" : "text-zinc-200"}`}>
                {s.status === "bad" ? "✗ " : s.status === "good" ? "✓ " : ""}
                {s.value}
              </dd>
            </div>
          ))}
        </dl>
      )}

      {result.timeline.events.length > 0 && (
        <div>
          <h4 className="mb-1.5 text-xs font-medium tracking-wide text-zinc-500 uppercase">What happened</h4>
          <ol className="space-y-0.5 text-xs">
            {result.timeline.events.map((e, i) => (
              <li key={i}>
                <button onClick={() => onSeek?.(e.t)} className="flex w-full gap-2 rounded px-1.5 py-0.5 text-left text-zinc-300 hover:bg-zinc-900">
                  <span className="w-14 shrink-0 text-right font-mono text-zinc-500">{Math.round(e.t)} ms</span>
                  <span className="w-3 text-center">{EVENT_ICONS[e.kind] ?? "•"}</span>
                  {e.message}
                </button>
              </li>
            ))}
          </ol>
        </div>
      )}

      {cost.items.some((i) => i.cost > 0) && (
        <details className="text-xs">
          <summary className={cost.budget && cost.total > cost.budget ? "text-red-400" : "text-zinc-400"}>
            Monthly cost: <span className="font-mono">${cost.total}</span>
            {cost.budget ? ` of a $${cost.budget} budget` : ""}
          </summary>
          <table className="mt-1.5 w-full">
            <tbody className="text-zinc-300">
              {cost.items
                .filter((i) => i.cost > 0)
                .map((i) => (
                  <tr key={i.nodeId} className="border-t border-zinc-800/70">
                    <td className="py-1">{i.label}</td>
                    <td className="py-1 text-zinc-500">{i.detail}</td>
                    <td className="py-1 text-right font-mono">${i.cost}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </details>
      )}

      {servers.length > 0 && (
        <table className="w-full text-xs">
          <thead className="text-left text-zinc-500">
            <tr>
              <th className="pb-1 font-normal">Node</th>
              <th className="pb-1 font-normal">CPU</th>
              <th className="pb-1 text-right font-normal">Requests</th>
              <th className="pb-1 text-right font-normal">Peak queue</th>
            </tr>
          </thead>
          <tbody className="text-zinc-300">
            {servers.map(([id, s]) => (
              <tr key={id} className="border-t border-zinc-800/70">
                <td className="py-1">{s.label}</td>
                <td className={`py-1 ${s.utilization >= 0.95 ? "text-red-400" : s.utilization >= 0.7 ? "text-amber-400" : "text-emerald-400"}`}>
                  {Math.round(s.utilization * 100)}%
                </td>
                <td className="py-1 text-right">{s.processed.toLocaleString()}</td>
                <td className="py-1 text-right">{s.maxQueue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function Metric({ label, value, bad }: { label: string; value: string; bad?: boolean }) {
  return (
    <div className="rounded border border-zinc-800 bg-zinc-900/60 px-3 py-2">
      <div className="text-[11px] text-zinc-500">{label}</div>
      <div className={`font-mono text-base ${bad ? "text-red-400" : "text-zinc-100"}`}>{value}</div>
    </div>
  );
}
