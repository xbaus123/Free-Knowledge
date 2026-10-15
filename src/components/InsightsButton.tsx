import { useEffect, useRef, useState } from "react";
import * as engine from "../lib/engine";
import { setTelemetryAllowed, telemetryAllowed } from "../lib/telemetry";

interface Props {
  courseId: string;
  lessonId: string;
  /** Saves the current visit first so the numbers are up to date. */
  flush: () => Promise<void>;
  /** Called when the learner turns recording on or off. */
  onAllowedChange: (allowed: boolean) => void;
  /** Called after this lesson's data is deleted, to start a fresh visit. */
  onCleared: () => void;
}

const OUTCOME_LABELS: Record<engine.Outcome, string> = {
  pass: "Passed",
  syntax_error: "Syntax errors",
  compile_error: "Compile errors",
  failed_assertion: "Failed tests",
  runtime_error: "Runtime errors",
  timeout: "Timeouts",
};

function duration(ms: number) {
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return m < 60 ? `${m}m ${s % 60}s` : `${Math.floor(m / 60)}h ${m % 60}m`;
}

/** Nav button with a popover of this lesson's local learning insights. */
export function InsightsButton({ courseId, lessonId, flush, onAllowedChange, onCleared }: Props) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<engine.Insights>();
  const [allowed, setAllowed] = useState(telemetryAllowed);
  const [error, setError] = useState<string>();
  const ref = useRef<HTMLDivElement>(null);

  const load = async () => {
    setError(undefined);
    try {
      await flush();
      setData(await engine.lessonInsights(courseId, lessonId));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    if (!open) return;
    void load();
    const onDown = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, courseId, lessonId]);

  const outcomes = Object.entries(data?.outcomes ?? {}).filter(([, n]) => n) as [engine.Outcome, number][];

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className={`rounded px-2 py-1 text-xs ${open ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"}`}
      >
        Insights
      </button>
      {open && (
        <div className="absolute top-full right-0 z-30 mt-1 w-80 rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm shadow-xl">
          <h3 className="mb-3 font-medium">Your learning on this lesson</h3>
          {error && <p className="mb-2 text-xs text-red-400">{error}</p>}
          {data && data.sessions > 0 ? (
            <>
              <dl className="mb-3 grid grid-cols-2 gap-2">
                <Stat label="Reading" value={duration(data.readingMs)} />
                <Stat label="Typing" value={duration(data.typingMs)} />
                <Stat label="Submissions" value={String(data.submissions)} />
                <Stat label="Time to solve" value={data.timeToSolveMs !== undefined ? duration(data.timeToSolveMs) : "not yet"} />
                {data.runs > 0 && <Stat label="Scratchpad runs" value={String(data.runs)} />}
                <Stat label="Visits" value={String(data.sessions)} />
              </dl>
              {outcomes.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-1.5">
                  {outcomes.map(([k, n]) => (
                    <span key={k} className={`rounded px-2 py-0.5 text-xs ${k === "pass" ? "bg-emerald-950 text-emerald-300" : "bg-zinc-800 text-zinc-300"}`}>
                      {OUTCOME_LABELS[k] ?? k}: {n}
                    </span>
                  ))}
                </div>
              )}
            </>
          ) : (
            <p className="mb-3 text-xs text-zinc-500">{allowed ? "Nothing recorded yet. Keep going!" : "Recording is off."}</p>
          )}
          <label className="mb-1 flex items-center gap-2 text-xs text-zinc-300">
            <input
              type="checkbox"
              checked={allowed}
              onChange={(e) => {
                setAllowed(e.target.checked);
                setTelemetryAllowed(e.target.checked);
                onAllowedChange(e.target.checked);
              }}
              className="accent-indigo-500"
            />
            Record learning insights on this device
          </label>
          <p className="mb-2 text-[11px] text-zinc-500">Times, attempt counts, and error types only. Never your code, and it never leaves this computer.</p>
          {data && data.sessions > 0 && (
            <button
              onClick={async () => {
                onCleared();
                await engine.deleteInsights(courseId, lessonId);
                setData(await engine.lessonInsights(courseId, lessonId));
              }}
              className="text-xs text-zinc-500 underline hover:text-red-400"
            >
              Clear this lesson's insights
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-zinc-800 bg-zinc-900/60 px-2.5 py-1.5">
      <dt className="text-[11px] text-zinc-500">{label}</dt>
      <dd className="font-mono text-zinc-100">{value}</dd>
    </div>
  );
}
