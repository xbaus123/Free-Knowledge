import { useEffect, useRef } from "react";
import type { GradeResult, TestResult } from "../lib/engine";

/** "info" lines are the app's own notes, like how a run ended. */
export type OutputLine = { stream: "stdout" | "stderr" | "info"; text: string };
export type Tab = "tests" | "output";

interface Props {
  tab: Tab;
  onTab: (tab: Tab) => void;
  output: OutputLine[];
  grade?: GradeResult;
  running: boolean;
  error?: string;
  onNext?: () => void;
}

const statusIcon: Record<TestResult["status"], string> = { pass: "✓", fail: "✗", error: "!", skip: "–" };
const statusColor: Record<TestResult["status"], string> = {
  pass: "text-emerald-400",
  fail: "text-red-400",
  error: "text-amber-400",
  skip: "text-zinc-500",
};

export function OutputPanel({ tab, onTab, output, grade, running, error, onNext }: Props) {
  const passed = grade?.tests.filter((t) => t.status === "pass").length ?? 0;
  const outputRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    const el = outputRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [output]);

  return (
    <div className="flex h-full flex-col bg-zinc-950">
      <div className="flex shrink-0 items-center gap-1 border-b border-zinc-800 px-2 text-xs">
        <TabButton active={tab === "tests"} onClick={() => onTab("tests")}>
          Tests{grade && grade.tests.length > 0 ? ` ${passed}/${grade.tests.length}` : ""}
        </TabButton>
        <TabButton active={tab === "output"} onClick={() => onTab("output")}>
          Output{output.length > 0 && tab !== "output" ? " •" : ""}
        </TabButton>
        <span className="ml-auto pr-1 text-zinc-500">{running ? "Running…" : grade ? `${grade.durationMs} ms` : ""}</span>
      </div>

      {tab === "tests" ? (
        <div className="min-h-0 flex-1 overflow-auto p-3 text-sm">
          {error && <p className="text-red-400">{error}</p>}
          {!grade && !error && !running && (
            <p className="text-zinc-500">
              Run the tests with <kbd className="rounded bg-zinc-800 px-1.5 py-0.5 text-xs">⌘ Enter</kbd> to check your solution.
            </p>
          )}
          {grade && <GradeSummary grade={grade} onNext={onNext} onShowOutput={() => onTab("output")} />}
        </div>
      ) : (
        <pre ref={outputRef} className="min-h-0 flex-1 overflow-auto p-3 font-mono text-[13px] whitespace-pre-wrap">
          {output.length === 0 ? (
            <span className="text-zinc-500">{running ? "" : "Your program's output will appear here."}</span>
          ) : (
            output.map((l, i) => (
              <span key={i} className={l.stream === "stderr" ? "text-red-300" : l.stream === "info" ? "mt-2 block text-zinc-500" : "text-zinc-200"}>
                {l.text}
              </span>
            ))
          )}
        </pre>
      )}
    </div>
  );
}

function GradeSummary({ grade, onNext, onShowOutput }: { grade: GradeResult; onNext?: () => void; onShowOutput: () => void }) {
  if (grade.error) return <p className="text-red-400">{grade.error}</p>;

  if (grade.phase === "compile") {
    return (
      <div>
        <p className="mb-2 font-medium text-red-400">Your code didn't compile.</p>
        <pre className="overflow-auto rounded bg-zinc-900 p-3 font-mono text-xs whitespace-pre-wrap text-red-200">
          {grade.stderr || grade.stdout || `compiler exited with code ${grade.exitCode}`}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {grade.passed ? (
        <div className="flex items-center justify-between rounded border border-emerald-800 bg-emerald-950/50 px-3 py-2">
          <span className="font-medium text-emerald-300">All tests passed. Nice work!</span>
          {onNext && (
            <button onClick={onNext} className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium hover:bg-emerald-500">
              Next lesson →
            </button>
          )}
        </div>
      ) : grade.timedOut ? (
        <p className="font-medium text-amber-400">Time limit exceeded. Is there an infinite loop?</p>
      ) : grade.tests.length === 0 ? (
        <div>
          <p className="mb-2 font-medium text-red-400">The tests couldn't run.</p>
          <pre className="overflow-auto rounded bg-zinc-900 p-3 font-mono text-xs whitespace-pre-wrap text-red-200">
            {grade.stderr || `exited with code ${grade.exitCode}`}
          </pre>
        </div>
      ) : null}

      {grade.tests.length > 0 && <TestList tests={grade.tests} />}

      {!grade.passed && grade.tests.length > 0 && (grade.stdout || grade.stderr) && (
        <button onClick={onShowOutput} className="text-xs text-zinc-400 underline hover:text-zinc-200">
          See program output
        </button>
      )}
      {grade.truncated && <p className="text-xs text-amber-400">Output was truncated at 1 MB.</p>}
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`border-b-2 px-2.5 py-2 ${active ? "border-indigo-500 text-zinc-100" : "border-transparent text-zinc-400 hover:text-zinc-200"}`}
    >
      {children}
    </button>
  );
}

export function TestList({ tests }: { tests: TestResult[] }) {
  return (
    <ul className="space-y-1.5">
      {tests.map((t) => (
        <li key={t.name}>
          <div className="flex items-baseline gap-2">
            <span className={`w-3 font-bold ${statusColor[t.status]}`}>{statusIcon[t.status]}</span>
            <span className={t.status === "pass" ? "text-zinc-300" : "text-zinc-100"}>{t.name}</span>
          </div>
          {t.status !== "pass" && hasDetails(t) ? (
            <FailureDetails test={t} />
          ) : (
            t.message &&
            t.status !== "pass" && (
              <pre className="mt-1 ml-5 overflow-auto rounded bg-zinc-900 p-2 font-mono text-xs whitespace-pre-wrap text-zinc-300">
                {t.message}
              </pre>
            )
          )}
        </li>
      ))}
    </ul>
  );
}

function hasDetails(t: TestResult) {
  return t.input !== undefined || t.expected !== undefined || t.actual !== undefined;
}

// FailureDetails shows a failed assertion's input and compared values, with
// the full assertion message (which may hold the test author's note) below.
function FailureDetails({ test }: { test: TestResult }) {
  return (
    <div className="mt-1 ml-5 space-y-1">
      {test.input !== undefined && <DetailBlock label="Input" value={test.input} className="border-zinc-700 bg-zinc-900 text-zinc-200" />}
      {test.expected !== undefined && (
        <DetailBlock label="Expected" value={test.expected} className="border-emerald-800 bg-emerald-950/40 text-emerald-200" />
      )}
      {test.actual !== undefined && (
        <DetailBlock label="Actual" value={test.actual} className="border-red-800 bg-red-950/40 text-red-200" />
      )}
      {test.message && (
        <details className="text-xs text-zinc-500">
          <summary className="cursor-pointer hover:text-zinc-300">Full message</summary>
          <pre className="mt-1 overflow-auto rounded bg-zinc-900 p-2 font-mono whitespace-pre-wrap text-zinc-300">{test.message}</pre>
        </details>
      )}
    </div>
  );
}

function DetailBlock({ label, value, className }: { label: string; value: string; className: string }) {
  return (
    <div className={`overflow-hidden rounded border ${className}`}>
      <div className="px-2 pt-1 text-[10px] font-semibold tracking-wide uppercase opacity-70">{label}</div>
      <pre className="overflow-auto px-2 pb-1.5 font-mono text-xs whitespace-pre-wrap">{value}</pre>
    </div>
  );
}
