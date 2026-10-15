import { useEffect, useRef, useState } from "react";
import * as engine from "../lib/engine";
import { CodeEditor } from "./CodeEditor";

interface Props {
  open: boolean;
  onClose: () => void;
  /** Called on each run, for lesson telemetry. */
  onRun?: () => void;
  /** Language to start in (the lesson's, if it has one). */
  defaultLanguage?: string;
}

const LANGUAGES = [
  { id: "python", name: "Python", ext: "py", sample: 'print("Hello from the scratchpad!")\n' },
  { id: "javascript", name: "JavaScript", ext: "js", sample: 'console.log("Hello from the scratchpad!");\n' },
  { id: "go", name: "Go", ext: "go", sample: 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("Hello from the scratchpad!")\n}\n' },
  { id: "c", name: "C", ext: "c", sample: '#include <stdio.h>\n\nint main(void) {\n    printf("Hello from the scratchpad!\\n");\n    return 0;\n}\n' },
  { id: "rust", name: "Rust", ext: "rs", sample: 'fn main() {\n    println!("Hello from the scratchpad!");\n}\n' },
];

const LANG_KEY = "fk:scratchpad:language";
const codeKey = (lang: string) => `fk:scratchpad:${lang}`;

function load(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function store(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Storage unavailable: the scratchpad still works, it just won't remember.
  }
}

type Line = { stream: "stdout" | "stderr" | "info"; text: string };

/** A slide-over code runner for trying things out, separate from the lesson's tests. */
export function ScratchpadModal({ open, onClose, onRun, defaultLanguage }: Props) {
  const [language, setLanguage] = useState(() => {
    const saved = load(LANG_KEY);
    return LANGUAGES.some((l) => l.id === saved) ? saved! : LANGUAGES.some((l) => l.id === defaultLanguage) ? defaultLanguage! : "python";
  });
  const lang = LANGUAGES.find((l) => l.id === language)!;
  const [code, setCode] = useState(() => load(codeKey(language)) ?? lang.sample);
  const codeRef = useRef(code);
  const [output, setOutput] = useState<Line[]>([]);
  const [running, setRunning] = useState(false);
  const cancelRef = useRef<() => void>(undefined);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const switchLanguage = (id: string) => {
    const next = LANGUAGES.find((l) => l.id === id)!;
    setLanguage(id);
    store(LANG_KEY, id);
    codeRef.current = load(codeKey(id)) ?? next.sample;
    setCode(codeRef.current);
    setOutput([]);
  };

  const run = async () => {
    if (cancelRef.current) return;
    onRun?.();
    setRunning(true);
    setOutput([]);
    const { result, cancel } = engine.runStreaming(
      { language, code: codeRef.current },
      {
        onOutput: (stream, text) =>
          setOutput((o) => {
            const last = o[o.length - 1];
            return last?.stream === stream ? [...o.slice(0, -1), { stream, text: last.text + text }] : [...o, { stream, text }];
          }),
      },
    );
    cancelRef.current = cancel;
    try {
      const r = await result;
      const status = r.error
        ? r.error
        : r.timedOut
          ? `Stopped: time limit reached after ${r.durationMs} ms`
          : r.phase === "compile" && r.exitCode !== 0
            ? "Didn't compile"
            : `Exited with code ${r.exitCode} in ${r.durationMs} ms`;
      setOutput((o) => [...o, { stream: "info", text: status }]);
    } catch (e) {
      if (!String(e).includes("cancelled")) setOutput((o) => [...o, { stream: "info", text: String(e) }]);
      else setOutput((o) => [...o, { stream: "info", text: "Stopped" }]);
    } finally {
      cancelRef.current = undefined;
      setRunning(false);
    }
  };

  // Kept mounted while closed so the editor and output survive reopening.
  return (
    <div className={open ? "" : "hidden"} aria-hidden={!open}>
      <div className="fixed inset-0 z-40 bg-black/40" onClick={onClose} />
      <aside
        role="dialog"
        aria-label="Scratchpad"
        className="fixed top-0 right-0 z-50 flex h-full w-full max-w-2xl flex-col border-l border-zinc-800 bg-zinc-950 shadow-2xl"
      >
        <header className="flex h-11 shrink-0 items-center gap-2 border-b border-zinc-800 px-3 text-sm">
          <span className="font-medium">Scratchpad</span>
          <span className="text-xs text-zinc-500">Try code freely. It isn't graded.</span>
          <div className="ml-auto flex items-center gap-2">
            <select value={language} onChange={(e) => switchLanguage(e.target.value)} disabled={running} className="rounded bg-zinc-800 px-2 py-1 text-xs" aria-label="Language">
              {LANGUAGES.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
            {running && (
              <button onClick={() => cancelRef.current?.()} className="rounded bg-red-700 px-3 py-1 text-xs font-medium hover:bg-red-600">
                Stop
              </button>
            )}
            <button onClick={run} disabled={running} title="⌘ Enter" className="rounded bg-indigo-600 px-3 py-1 text-xs font-medium hover:bg-indigo-500 disabled:opacity-40">
              {running ? "Running…" : "▶ Run"}
            </button>
            <button onClick={onClose} aria-label="Close scratchpad" title="Close (Esc)" className="rounded px-2 py-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
              ✕
            </button>
          </div>
        </header>
        <div className="min-h-0 flex-[3]">
          {open && (
            <CodeEditor
              path={`scratchpad/main.${lang.ext}`}
              language={language}
              value={code}
              onChange={(v) => {
                codeRef.current = v;
                setCode(v);
                store(codeKey(language), v);
              }}
              onSubmit={run}
            />
          )}
        </div>
        <pre className="min-h-0 flex-[2] overflow-auto border-t border-zinc-800 bg-black p-3 font-mono text-[13px] whitespace-pre-wrap">
          {output.length === 0 ? (
            <span className="text-zinc-500">Output appears here. Press ⌘ Enter to run.</span>
          ) : (
            output.map((l, i) => (
              <span key={i} className={l.stream === "stderr" ? "text-red-300" : l.stream === "info" ? "mt-2 block text-zinc-500" : "text-zinc-200"}>
                {l.text}
              </span>
            ))
          )}
        </pre>
      </aside>
    </div>
  );
}
