import { useCallback, useEffect, useRef, useState } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import * as engine from "../lib/engine";
import { CodeEditor } from "./CodeEditor";
import { SimulationPanel } from "./design/SimulationPanel";
import { SystemCanvas } from "./design/SystemCanvas";
import { QuizPanel } from "./quiz/QuizPanel";
import { Markdown } from "./Markdown";
import { OutputPanel, type OutputLine, type Tab } from "./OutputPanel";

interface Props {
  courseId: string;
  lessonId: string;
  onOpenLesson: (lessonId: string) => void;
  onHome: () => void;
  /** Label for the back button; "Courses" unless previewing from the Studio. */
  backLabel?: string;
}

type SaveState = "saved" | "unsaved" | "saving" | "error";

const AUTOSAVE_MS = 800;

export function Workspace({ courseId, lessonId, onOpenLesson, onHome, backLabel = "Courses" }: Props) {
  const [course, setCourse] = useState<engine.Course>();
  const [progress, setProgress] = useState<Record<string, engine.LessonProgress>>({});
  const [lesson, setLesson] = useState<engine.Lesson>();
  const [code, setCode] = useState("");
  // Mirrors `code` synchronously: ⌘Enter can fire right after a keystroke,
  // before React re-renders with the new state.
  const codeRef = useRef("");
  const [loadError, setLoadError] = useState<string>();
  const [saveState, setSaveState] = useState<SaveState>("saved");

  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<OutputLine[]>([]);
  const [grade, setGrade] = useState<engine.GradeResult>();
  const [runError, setRunError] = useState<string>();
  const [tab, setTab] = useState<Tab>("tests");
  const [confirmReset, setConfirmReset] = useState(false);
  const cancelRef = useRef<() => void>(undefined);

  // System design lessons
  const [simResult, setSimResult] = useState<engine.SimResult>();
  // The diagram changed since the last run, so node overlays would mislead.
  const [simStale, setSimStale] = useState(false);
  // Bumped to remount the canvas with a new diagram (reset to starter).
  const [canvasKey, setCanvasKey] = useState(0);
  const isDesign = engine.isDesignLesson(lesson);
  const isArticle = engine.isArticleLesson(lesson);
  const isQuiz = engine.isQuizLesson(lesson);
  // Quizzes save the last answer as {"answer": N}.
  const [quizAnswer, setQuizAnswer] = useState<number>();
  const [marking, setMarking] = useState(false);

  const refreshProgress = useCallback(() => {
    engine
      .progress()
      .then((p) => setProgress(p.courses[courseId] ?? {}))
      .catch(console.error);
  }, [courseId]);

  useEffect(() => {
    engine.course(courseId).then(setCourse, (e) => setLoadError(String(e)));
    refreshProgress();
  }, [courseId, refreshProgress]);

  // Load the lesson and the learner's saved code, falling back to the starter.
  useEffect(() => {
    let stale = false;
    setLesson(undefined);
    setLoadError(undefined);
    setGrade(undefined);
    setOutput([]);
    setRunError(undefined);
    setTab("tests");
    setConfirmReset(false);
    setSimResult(undefined);
    Promise.all([engine.lesson(courseId, lessonId), engine.lessonProgress(courseId, lessonId)])
      .then(([l, p]) => {
        if (stale) return;
        setLesson(l);
        setQuizAnswer(engine.isQuizLesson(l) ? parseQuizAnswer(p.code) : undefined);
        codeRef.current = p.code ?? l.starter;
        setCode(codeRef.current);
        setSaveState("saved");
      })
      .catch((e) => !stale && setLoadError(String(e)));
    return () => {
      stale = true;
      cancelRef.current?.();
    };
  }, [courseId, lessonId]);

  // --- autosave ---
  const pending = useRef<{ courseId: string; lessonId: string; code: string } | null>(null);
  const timer = useRef<number>(undefined);

  const flushSave = useCallback(async () => {
    window.clearTimeout(timer.current);
    const p = pending.current;
    if (!p) return;
    pending.current = null;
    setSaveState("saving");
    try {
      await engine.saveCode(p.courseId, p.lessonId, p.code);
      if (!pending.current) setSaveState("saved");
    } catch (e) {
      console.error("autosave failed", e);
      setSaveState("error");
    }
  }, []);

  // Save immediately when leaving a lesson or closing the workspace.
  useEffect(() => () => void flushSave(), [courseId, lessonId, flushSave]);

  const onCodeChange = (value: string) => {
    setSimStale(true);
    codeRef.current = value;
    setCode(value);
    pending.current = { courseId, lessonId, code: value };
    setSaveState("unsaved");
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(flushSave, AUTOSAVE_MS);
  };

  // --- grading ---
  const submit = useCallback(async () => {
    // Articles and quizzes have their own buttons.
    if (!lesson || cancelRef.current || engine.isArticleLesson(lesson) || engine.isQuizLesson(lesson)) return;
    // Save now: a stopped run isn't recorded, so the code must not depend on it.
    void flushSave();

    if (engine.isDesignLesson(lesson)) {
      cancelRef.current = () => {}; // blocks a second run; simulations can't be stopped
      setRunning(true);
      setRunError(undefined);
      try {
        // Keep the traffic animation on screen briefly; the simulation itself takes milliseconds.
        const [r] = await Promise.all([engine.simulate(courseId, lessonId, codeRef.current), new Promise((ok) => setTimeout(ok, 700))]);
        setSimResult(r);
        setSimStale(false);
        setSaveState("saved");
        refreshProgress();
      } catch (e) {
        setRunError(e instanceof Error ? e.message : String(e));
      } finally {
        cancelRef.current = undefined;
        setRunning(false);
      }
      return;
    }

    setRunning(true);
    setOutput([]);
    setGrade(undefined);
    setRunError(undefined);
    setTab("tests");
    const { result, cancel } = engine.submitStreaming(courseId, lessonId, codeRef.current, {
      onOutput: (stream, text) =>
        setOutput((o) => {
          const last = o[o.length - 1];
          return last?.stream === stream ? [...o.slice(0, -1), { stream, text: last.text + text }] : [...o, { stream, text }];
        }),
    });
    cancelRef.current = cancel;
    try {
      const g = await result;
      setGrade(g);
      setSaveState("saved");
      refreshProgress();
    } catch (e) {
      if (!String(e).includes("cancelled")) setRunError(String(e));
    } finally {
      cancelRef.current = undefined;
      setRunning(false);
    }
  }, [lesson, courseId, lessonId, refreshProgress, flushSave]);

  // ⌘/Ctrl+Enter anywhere (Monaco handles it itself while focused).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !e.defaultPrevented) {
        e.preventDefault();
        submit();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [submit]);

  const markComplete = async () => {
    setMarking(true);
    setRunError(undefined);
    try {
      await engine.completeArticle(courseId, lessonId);
      refreshProgress();
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setMarking(false);
    }
  };

  const submitAnswer = async (answer: number) => {
    const res = await engine.submitAnswer(courseId, lessonId, answer);
    refreshProgress();
    return res;
  };

  const reset = async () => {
    if (!lesson) return;
    window.clearTimeout(timer.current);
    pending.current = null;
    setConfirmReset(false);
    codeRef.current = lesson.starter;
    setCode(lesson.starter);
    setCanvasKey((k) => k + 1);
    setSimResult(undefined);
    try {
      await engine.resetCode(courseId, lessonId);
      setSaveState("saved");
    } catch {
      setSaveState("error");
    }
  };

  const lessons = course?.lessons ?? [];
  const index = lessons.findIndex((l) => l.id === lessonId);
  const prev = index > 0 ? lessons[index - 1] : undefined;
  const next = index >= 0 && index < lessons.length - 1 ? lessons[index + 1] : undefined;
  const completedCount = lessons.filter((l) => progress[l.id]?.completed).length;

  const completed = !!progress[lessonId]?.completed;
  const goNext = next ? () => onOpenLesson(next.id) : undefined;

  const lessonPane = (
    <div className="h-full overflow-auto px-6 py-5">
      {lesson ? (
        <>
          {progress[lesson.id]?.completed && (
            <p className="mb-3 inline-block rounded bg-emerald-950 px-2 py-0.5 text-xs text-emerald-300">✓ Completed</p>
          )}
          {lesson.problems && lesson.problems.length > 0 && (
            <div className="mb-4 rounded border border-amber-800 bg-amber-950/40 p-3 text-xs text-amber-200">
              This lesson has problems and can't be graded:
              <ul className="mt-1 list-disc pl-5">
                {lesson.problems.map((p) => (
                  <li key={p}>{p}</li>
                ))}
              </ul>
            </div>
          )}
          <Markdown>{lesson.markdown}</Markdown>
        </>
      ) : (
        <p className="text-sm text-zinc-500">Loading…</p>
      )}
    </div>
  );

  return (
    <div className="flex h-full flex-col">
      <header className="flex h-11 shrink-0 items-center gap-3 border-b border-zinc-800 bg-zinc-950 px-3 text-sm">
        <button onClick={onHome} className="rounded px-2 py-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
          ← {backLabel}
        </button>
        <span className="truncate text-zinc-500">{course?.title}</span>
        <span className="text-zinc-700">/</span>
        <select
          value={lessonId}
          onChange={(e) => onOpenLesson(e.target.value)}
          className="max-w-xs truncate rounded bg-transparent px-1 py-1 font-medium text-zinc-100 hover:bg-zinc-800"
        >
          {lessons.map((l, i) => (
            <option key={l.id} value={l.id}>
              {progress[l.id]?.completed ? "✓ " : ""}
              {i + 1}. {l.title}
            </option>
          ))}
        </select>
        <span className="text-xs text-zinc-500">
          {completedCount}/{lessons.length} done
        </span>
        <div className="ml-auto flex items-center gap-1">
          <NavButton disabled={!prev} onClick={() => prev && onOpenLesson(prev.id)}>
            ‹ Prev
          </NavButton>
          <NavButton disabled={!next} onClick={() => next && onOpenLesson(next.id)}>
            Next ›
          </NavButton>
        </div>
      </header>

      {loadError ? (
        <div className="p-6 text-red-400">{loadError}</div>
      ) : isArticle && lesson ? (
        <div className="min-h-0 flex-1 overflow-auto">
          <article className="mx-auto max-w-3xl px-8 py-10">
            <Markdown>{lesson.markdown}</Markdown>
            <div className="mt-10 flex items-center justify-between gap-4 border-t border-zinc-800 pt-6">
              {completed ? (
                <span className="text-sm text-emerald-400">✓ Completed</span>
              ) : (
                <button
                  onClick={markComplete}
                  disabled={marking}
                  className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
                >
                  {marking ? "Saving…" : "Mark Complete"}
                </button>
              )}
              {runError && <span className="text-sm text-red-400">{runError}</span>}
              {completed && goNext && (
                <button onClick={goNext} className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500">
                  Next lesson →
                </button>
              )}
            </div>
          </article>
        </div>
      ) : isQuiz && lesson ? (
        <Group orientation="horizontal" className="min-h-0 flex-1">
          <Panel id="lesson" defaultSize="50" minSize="25">
            {lessonPane}
          </Panel>
          <Separator className="w-px bg-zinc-800 transition-colors hover:bg-indigo-500 data-[separator=active]:bg-indigo-500" />
          <Panel id="quiz" minSize="30">
            <QuizPanel
              key={`${courseId}/${lessonId}`}
              options={lesson.options ?? []}
              initialAnswer={quizAnswer}
              completed={completed}
              onSubmit={submitAnswer}
              onNext={goNext}
            />
          </Panel>
        </Group>
      ) : (
        <Group orientation="horizontal" className="min-h-0 flex-1">
          <Panel id="lesson" defaultSize="42" minSize="20">
            {lessonPane}
          </Panel>
          <Separator className="w-px bg-zinc-800 transition-colors hover:bg-indigo-500 data-[separator=active]:bg-indigo-500" />
          <Panel id="work" minSize="30">
            <Group orientation="vertical">
              <Panel id="editor" defaultSize="65" minSize="20">
                <div className="flex h-full flex-col">
                  <div className="flex h-10 shrink-0 items-center gap-2 border-b border-zinc-800 bg-zinc-950 px-3 text-sm">
                    <span className="rounded bg-zinc-800 px-2 py-0.5 font-mono text-xs text-zinc-300">
                      {isDesign ? "architecture" : `solution.${extension(lesson?.language)}`}
                    </span>
                    <SaveIndicator state={saveState} />
                    <div className="ml-auto flex items-center gap-2">
                      {confirmReset ? (
                        <>
                          <span className="text-xs text-zinc-400">Replace your {isDesign ? "diagram" : "code"} with the starter?</span>
                          <button onClick={reset} className="rounded bg-red-700 px-2 py-1 text-xs hover:bg-red-600">
                            Reset
                          </button>
                          <button onClick={() => setConfirmReset(false)} className="rounded px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800">
                            Cancel
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setConfirmReset(true)}
                          disabled={!lesson || running}
                          className="rounded px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 disabled:opacity-40"
                        >
                          Reset
                        </button>
                      )}
                      {/* Stop sits beside Run (not in its place) so a double-click can't restart the run. */}
                      {running && !isDesign && (
                        <button onClick={() => cancelRef.current?.()} className="rounded bg-red-700 px-3 py-1 font-medium hover:bg-red-600">
                          Stop
                        </button>
                      )}
                      <button
                        onClick={submit}
                        disabled={running || !lesson || !!lesson.problems?.length}
                        title="⌘ Enter"
                        className="rounded bg-indigo-600 px-3 py-1 font-medium hover:bg-indigo-500 disabled:opacity-40"
                      >
                        {isDesign ? (running ? "Simulating…" : "▶ Simulate Traffic") : running ? "Running…" : "▶ Run tests"}
                      </button>
                    </div>
                  </div>
                  <div className="min-h-0 flex-1">
                    {lesson && isDesign && (
                      <SystemCanvas
                        key={`${courseId}/${lessonId}/${canvasKey}`}
                        initial={code}
                        onChange={onCodeChange}
                        result={simStale ? undefined : simResult}
                        running={running}
                      />
                    )}
                    {lesson && !isDesign && (
                      <CodeEditor
                        path={`${courseId}/${lessonId}/solution.${extension(lesson.language)}`}
                        language={lesson.language}
                        value={code}
                        onChange={onCodeChange}
                        onSubmit={submit}
                      />
                    )}
                  </div>
                </div>
              </Panel>
              <Separator className="h-px bg-zinc-800 transition-colors hover:bg-indigo-500 data-[separator=active]:bg-indigo-500" />
              <Panel id="output" defaultSize="35" minSize="10">
                {isDesign ? (
                  <SimulationPanel
                    result={simResult}
                    running={running}
                    error={runError}
                    maxLatencyMs={lesson?.maxLatencyMs}
                    stale={simStale && !!simResult}
                    onNext={next ? () => onOpenLesson(next.id) : undefined}
                  />
                ) : (
                  <OutputPanel
                    tab={tab}
                    onTab={setTab}
                    output={output}
                    grade={grade}
                    running={running}
                    error={runError}
                    onNext={next ? () => onOpenLesson(next.id) : undefined}
                  />
                )}
              </Panel>
            </Group>
          </Panel>
        </Group>
      )}
    </div>
  );
}

function parseQuizAnswer(saved: string | null): number | undefined {
  try {
    const a = saved ? JSON.parse(saved).answer : undefined;
    return typeof a === "number" ? a : undefined;
  } catch {
    return undefined;
  }
}

function extension(language?: string) {
  return ({ python: "py", javascript: "js", go: "go", c: "c", rust: "rs" } as Record<string, string>)[language ?? ""] ?? "txt";
}

function SaveIndicator({ state }: { state: SaveState }) {
  const label = { saved: "Saved", unsaved: "Editing…", saving: "Saving…", error: "Couldn't save" }[state];
  return <span className={`text-xs ${state === "error" ? "text-red-400" : "text-zinc-500"}`}>{label}</span>;
}

function NavButton({ disabled, onClick, children }: { disabled: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className="rounded px-2 py-1 text-zinc-300 hover:bg-zinc-800 disabled:text-zinc-700 disabled:hover:bg-transparent"
    >
      {children}
    </button>
  );
}
