import type { SimResult } from "../../lib/engine";

interface Props {
  result?: SimResult;
  running: boolean;
  error?: string;
  maxLatencyMs?: number;
  /** The diagram changed after this result was produced. */
  stale?: boolean;
  onNext?: () => void;
}

export function SimulationPanel({ result, running, error, maxLatencyMs, stale, onNext }: Props) {
  return (
    <div className="flex h-full flex-col bg-zinc-950">
      <div className="flex shrink-0 items-center border-b border-zinc-800 px-3 py-2 text-xs">
        <span className="font-medium text-zinc-200">Simulation</span>
        <span className="ml-auto text-zinc-500">
          {running ? "Sending traffic…" : maxLatencyMs ? `Goal: p99 ≤ ${maxLatencyMs} ms for 1,000 requests` : ""}
        </span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto p-3 text-sm">
        {error && <p className="text-red-400">{error}</p>}
        {!result && !error && !running && (
          <p className="text-zinc-500">
            Click <span className="text-zinc-300">Simulate Traffic</span> (or press <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs">⌘ Enter</kbd>)
            to send a burst of 1,000 requests through your design.
          </p>
        )}
        {result && stale && !running && (
          <p className="mb-3 text-xs text-zinc-500">You've changed the diagram since this run. Simulate again to see how it performs.</p>
        )}
        {result && <Summary result={result} onNext={onNext} />}
      </div>
    </div>
  );
}

function Summary({ result, onNext }: { result: SimResult; onNext?: () => void }) {
  const m = result.metrics;
  const overTarget = m.maxLatencyMs !== undefined && m.p99Ms > m.maxLatencyMs;
  const servers = Object.entries(result.nodes)
    .filter(([, s]) => s.type === "server" || s.type === "database")
    .sort(([, a], [, b]) => b.utilization - a.utilization);

  return (
    <div className="space-y-4">
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

      {m.completed > 0 && (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Metric label="p50 latency" value={`${m.p50Ms} ms`} />
          <Metric label="p99 latency" value={`${m.p99Ms} ms`} bad={overTarget} />
          <Metric label="throughput" value={`${m.throughputPerSec.toLocaleString()}/s`} />
          <Metric label="answered" value={`${m.completed.toLocaleString()} / ${m.requests.toLocaleString()}`} bad={m.failed > 0} />
        </div>
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
