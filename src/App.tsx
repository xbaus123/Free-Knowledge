// Temporary diagnostics screen for Step 2: confirms the engine is reachable
// and that /run and streaming runs work. Replaced by the workspace UI in Step 3.
import { useEffect, useRef, useState } from "react";
import * as engine from "./lib/engine";

const SAMPLES: Record<string, string> = {
  python: 'import time\nfor i in range(5):\n    print(f"tick {i}")\n    time.sleep(0.3)\n',
  javascript: 'for (let i = 0; i < 5; i++) console.log("tick", i);\n',
  go: 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("hello from go")\n}\n',
  c: '#include <stdio.h>\n\nint main(void) {\n    printf("hello from c\\n");\n    return 0;\n}\n',
  rust: 'fn main() {\n    println!("hello from rust");\n}\n',
};

type Line = { stream: "stdout" | "stderr" | "info"; text: string };

export default function App() {
  const [status, setStatus] = useState<"connecting" | "ok" | "down">("connecting");
  const [version, setVersion] = useState("");
  const [statusError, setStatusError] = useState("");
  const [runtimes, setRuntimes] = useState<engine.RuntimeInfo[]>([]);
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(SAMPLES.python);
  const [output, setOutput] = useState<Line[]>([]);
  const [running, setRunning] = useState(false);
  const cancelRef = useRef<() => void>(undefined);

  useEffect(() => {
    engine
      .waitForEngine()
      .then(async (h) => {
        setStatus("ok");
        setVersion(h.version);
        setRuntimes(await engine.runtimes());
      })
      .catch((err) => {
        setStatus("down");
        setStatusError(String(err));
      });
  }, []);

  const append = (line: Line) => setOutput((o) => [...o, line]);

  const summarize = (r: engine.RunResult) =>
    append({
      stream: "info",
      text: r.error
        ? `engine error: ${r.error}`
        : `[${r.phase}] exit ${r.exitCode} in ${r.durationMs}ms${r.timedOut ? " (timed out)" : ""}${r.truncated ? " (output truncated)" : ""}`,
    });

  async function runHttp() {
    setOutput([]);
    setRunning(true);
    try {
      const r = await engine.run({ language, code });
      if (r.stdout) append({ stream: "stdout", text: r.stdout });
      if (r.stderr) append({ stream: "stderr", text: r.stderr });
      summarize(r);
    } catch (err) {
      append({ stream: "info", text: String(err) });
    } finally {
      setRunning(false);
    }
  }

  async function runStream() {
    setOutput([]);
    setRunning(true);
    const { result, cancel } = engine.runStreaming({ language, code }, {
      onOutput: (stream, text) => append({ stream, text }),
    });
    cancelRef.current = cancel;
    try {
      summarize(await result);
    } catch (err) {
      append({ stream: "info", text: String(err) });
    } finally {
      cancelRef.current = undefined;
      setRunning(false);
    }
  }

  return (
    <main className="flex h-screen flex-col gap-4 bg-zinc-950 p-6 text-zinc-100">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">FreeKnowledge · Engine diagnostics</h1>
        <span className="flex items-center gap-2 text-sm">
          <span
            className={`h-2.5 w-2.5 rounded-full ${
              status === "ok" ? "bg-emerald-400" : status === "down" ? "bg-red-500" : "bg-amber-400"
            }`}
          />
          {status === "ok" ? `engine v${version}` : status === "down" ? "engine unreachable" : "connecting…"}
        </span>
      </header>
      {statusError && <p className="text-sm text-red-400">{statusError}</p>}

      <section className="flex flex-wrap gap-2 text-xs">
        {runtimes.map((r) => (
          <span
            key={r.id}
            title={r.path ?? `${r.requires} not found`}
            className={`rounded px-2 py-1 ${r.available ? "bg-emerald-900/60 text-emerald-200" : "bg-zinc-800 text-zinc-500 line-through"}`}
          >
            {r.name}
          </span>
        ))}
      </section>

      <div className="flex items-center gap-2">
        <select
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value);
            setCode(SAMPLES[e.target.value] ?? "");
          }}
          className="rounded bg-zinc-800 px-2 py-1.5 text-sm"
        >
          {Object.keys(SAMPLES).map((id) => (
            <option key={id} value={id}>
              {runtimes.find((r) => r.id === id)?.name ?? id}
            </option>
          ))}
        </select>
        <button
          onClick={runHttp}
          disabled={running || status !== "ok"}
          className="rounded bg-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-600 disabled:opacity-40"
        >
          Run (HTTP)
        </button>
        <button
          onClick={runStream}
          disabled={running || status !== "ok"}
          className="rounded bg-indigo-600 px-3 py-1.5 text-sm hover:bg-indigo-500 disabled:opacity-40"
        >
          Run (stream)
        </button>
        {running && cancelRef.current && (
          <button onClick={() => cancelRef.current?.()} className="rounded bg-red-700 px-3 py-1.5 text-sm hover:bg-red-600">
            Stop
          </button>
        )}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-2 gap-4">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          className="resize-none rounded bg-zinc-900 p-3 font-mono text-sm outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <pre className="overflow-auto rounded bg-black p-3 font-mono text-sm whitespace-pre-wrap">
          {output.map((l, i) => (
            <span
              key={i}
              className={l.stream === "stderr" ? "text-red-400" : l.stream === "info" ? "mt-2 block text-zinc-500" : ""}
            >
              {l.text}
            </span>
          ))}
        </pre>
      </div>
    </main>
  );
}
