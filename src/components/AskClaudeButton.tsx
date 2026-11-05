import { openUrl } from "@tauri-apps/plugin-opener";
import { useEffect, useRef, useState } from "react";
import type * as engine from "../lib/engine";
import type { OutputLine } from "./OutputPanel";

interface Props {
  lesson: engine.Lesson;
  courseTitle?: string;
  /** The learner's current code, keyed by file name. */
  files: Record<string, string>;
  /** The latest test run, if any. */
  grade?: engine.GradeResult;
  /** Streamed output from the latest run or test run. */
  output: OutputLine[];
  /** An error from the latest run that never produced a result. */
  runError?: string;
}

// Deep links carry the whole prompt in the URL, so keep each part bounded.
const MAX_LESSON = 6000;
const MAX_FILE = 6000;
const MAX_OUTPUT = 3000;

type Status = "idle" | "opened" | "copied" | "failed";

/** Opens the Claude desktop app with a Socratic-hint prompt built from the workspace. */
export function AskClaudeButton({ lesson, courseTitle, files, grade, output, runError }: Props) {
  const [status, setStatus] = useState<Status>("idle");
  const timer = useRef<number>(undefined);
  useEffect(() => () => window.clearTimeout(timer.current), []);

  const flash = (s: Status) => {
    setStatus(s);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setStatus("idle"), 3000);
  };

  const ask = async () => {
    const prompt = buildPrompt({ lesson, courseTitle, files, grade, output, runError });
    try {
      await openUrl(`claude://claude.ai/new?q=${encodeURIComponent(prompt)}`);
      flash("opened");
    } catch (e) {
      console.warn("Couldn't open the Claude app, copying the prompt instead", e);
      try {
        await navigator.clipboard.writeText(prompt);
        flash("copied");
      } catch (err) {
        console.error("Couldn't copy the prompt", err);
        flash("failed");
      }
    }
  };

  const label = { idle: "✦ Ask Claude", opened: "Opened in Claude", copied: "Prompt copied", failed: "Couldn't open Claude" }[status];

  return (
    <button
      onClick={ask}
      title={
        status === "copied"
          ? "The Claude app couldn't be opened, so the prompt was copied. Paste it into Claude."
          : "Ask Claude for a hint about this lesson (no solutions, just guidance)"
      }
      className={`rounded px-2 py-1 text-xs ${status === "failed" ? "text-red-400" : status === "idle" ? "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100" : "text-emerald-400"}`}
    >
      {label}
    </button>
  );
}

function clip(text: string, max: number) {
  return text.length > max ? `${text.slice(0, max)}\n… (truncated, ${text.length - max} more characters)` : text;
}

/** A fence that the content can't close early. */
function fence(text: string, lang = "") {
  const ticks = "`".repeat(Math.max(3, ...[...text.matchAll(/`+/g)].map((m) => m[0].length + 1)));
  return `${ticks}${lang}\n${text}\n${ticks}`;
}

export function buildPrompt({ lesson, courseTitle, files, grade, output, runError }: Props): string {
  const parts: string[] = [];

  parts.push(
    `I'm working through a coding lesson in an offline learning app and I'm stuck. Please act as a Socratic tutor.

Rules for your reply:
- Do NOT write the solution or give me code that solves the exercise, not even partially or as pseudocode I could copy.
- Give me ONE conceptual hint or a guiding question that points me toward the bug or the idea I'm missing.
- If my tests show a specific failure, help me reason about why that input gives that result, without telling me the fix.
- Keep it short. I want to figure it out myself.`,
  );

  parts.push(`## Lesson: ${lesson.title}${courseTitle ? ` (${courseTitle})` : ""}\nLanguage: ${lesson.language}\n\n${clip(lesson.markdown.trim(), MAX_LESSON)}`);

  const fileEntries = Object.entries(files);
  parts.push(
    `## My current code\n\n${fileEntries.length ? fileEntries.map(([path, content]) => `${path}:\n${fence(clip(content, MAX_FILE), lesson.language)}`).join("\n\n") : "(empty)"}`,
  );

  parts.push(`## Latest results\n\n${describeResults(grade, output, runError)}`);

  return parts.join("\n\n");
}

function describeResults(grade: engine.GradeResult | undefined, output: OutputLine[], runError?: string): string {
  const lines: string[] = [];
  if (runError) lines.push(`Error: ${runError}`);
  if (grade) {
    if (grade.error) lines.push(`Error: ${grade.error}`);
    if (grade.timedOut) lines.push(`The tests timed out after ${grade.durationMs} ms.`);
    const passed = grade.tests.filter((t) => t.status === "pass").length;
    lines.push(`Tests: ${passed}/${grade.tests.length} passing${grade.passed ? " (all passed)" : ""}, phase: ${grade.phase}.`);
    for (const t of grade.tests.filter((t) => t.status !== "pass")) {
      const detail = [
        t.input && `input: ${t.input}`,
        t.expected !== undefined && `expected: ${t.expected}`,
        t.actual !== undefined && `actual: ${t.actual}`,
        t.message && `message: ${t.message}`,
      ].filter(Boolean);
      lines.push(`- ${t.status.toUpperCase()} ${t.name}${detail.length ? `\n  ${detail.join("\n  ")}` : ""}`);
    }
  }
  const out = output
    .map((o) => o.text)
    .join("")
    .trim();
  const compiler = grade && !grade.tests.length ? `${grade.stdout}\n${grade.stderr}`.trim() : "";
  const shown = out || compiler;
  if (shown) lines.push(`Output:\n${fence(clip(shown, MAX_OUTPUT))}`);
  return lines.length ? lines.join("\n") : "I haven't run the tests yet.";
}
