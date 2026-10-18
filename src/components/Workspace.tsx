import { useCallback, useEffect, useRef, useState } from "react";
import { Group, Panel, Separator } from "react-resizable-panels";
import * as engine from "../lib/engine";
import { languageForPath } from "../lib/monaco";
import { classifyGrade, LessonTelemetry, telemetryAllowed } from "../lib/telemetry";
import { CodeEditor } from "./CodeEditor";
import { FileTree, LockIcon } from "./FileTree";
import { InsightsButton } from "./InsightsButton";
import { ScratchpadModal } from "./ScratchpadModal";
import { SimulationPanel } from "./design/SimulationPanel";
import { parseGraph, SystemCanvas } from "./design/SystemCanvas";
import { TimelineScrubber } from "./design/TimelineScrubber";
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
  // Replay of the last simulation.
  const [frame, setFrame] = useState(0);
  const [playing, setPlaying] = useState(false);
  // Chaos experiments: nodes to crash and edges to cut.
  const [chaos, setChaos] = useState<engine.Chaos>({ nodes: [], edges: [] });
  const chaosRef = useRef(chaos);
  chaosRef.current = chaos;
  const isDesign = engine.isDesignLesson(lesson);
  const isArticle = engine.isArticleLesson(lesson);
  const isQuiz = engine.isQuizLesson(lesson);
  // Quizzes save the last answers as {"answers": [...]}.
  const [quizAnswers, setQuizAnswers] = useState<number[]>();
  const [marking, setMarking] = useState(false);

  // Capabilities
  const caps = lesson?.capabilities;
  const multiFile = !!caps?.multi_file && lesson?.kind === "code";
  // Multi-file lessons: every file's current content (read-only ones included).
  const [files, setFiles] = useState<Record<string, string>>({});
  const filesRef = useRef(files);
  const [openTabs, setOpenTabs] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState("");
  const [scratchpadOpen, setScratchpadOpen] = useState(false);
  const telemetry = useRef<LessonTelemetry | null>(null);
  const [telemetryOn, setTelemetryOn] = useState(telemetryAllowed);
  const [telemetryEpoch, setTelemetryEpoch] = useState(0); // bumped to start a fresh visit

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
    setChaos({ nodes: [], edges: [] });
    setPlaying(false);
    Promise.all([engine.lesson(courseId, lessonId), engine.lessonProgress(courseId, lessonId)])
      .then(([l, p]) => {
        if (stale) return;
        setLesson(l);
        setQuizAnswers(engine.isQuizLesson(l) ? parseQuizAnswers(p.code) : undefined);
        codeRef.current = p.code ?? l.starter;
        if (l.capabilities.multi_file && l.files?.length) {
          const all = restoreFiles(l, p.code);
          filesRef.current = all;
          setFiles(all);
          codeRef.current = editableFilesJSON(l, all);
          const first = l.files.find((f) => !f.readOnly && f.path.startsWith("solution.")) ?? l.files.find((f) => !f.readOnly) ?? l.files[0];
          setActiveFile(first.path);
          setOpenTabs([first.path]);
        }
        setCode(codeRef.current);
        setSaveState("saved");
      })
      .catch((e) => !stale && setLoadError(String(e)));
    return () => {
      stale = true;
      cancelRef.current?.();
    };
  }, [courseId, lessonId]);

  // --- telemetry: one tracked visit per lesson, if the lesson and learner allow it ---
  useEffect(() => {
    if (!lesson?.capabilities.telemetry || !telemetryOn) return;
    const t = new LessonTelemetry(courseId, lesson.id);
    telemetry.current = t;
    return () => {
      t.dispose();
      if (telemetry.current === t) telemetry.current = null;
    };
  }, [lesson, courseId, telemetryOn, telemetryEpoch]);

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
    telemetry.current?.keystroke();
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
      setPlaying(false);
      try {
        // Only chaos targets that still exist in the diagram.
        const graph = parseGraph(codeRef.current);
        const c = chaosRef.current;
        const live = {
          nodes: c.nodes.filter((id) => graph.nodes.some((n) => n.id === id)),
          edges: c.edges.filter((id) => graph.edges.some((e) => e.id === id)),
        };
        // Keep the traffic animation on screen briefly; the simulation itself takes milliseconds.
        const [r] = await Promise.all([engine.simulate(courseId, lessonId, codeRef.current, live), new Promise((ok) => setTimeout(ok, 500))]);
        setSimResult(r);
        setSimStale(false);
        setFrame(0);
        setPlaying(r.timeline.frames.length > 0);
        if (r.experiment) telemetry.current?.run();
        else telemetry.current?.submission(r.passed ? "pass" : "failed_assertion");
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
    const handlers: engine.StreamHandlers = {
      onOutput: (stream, text) =>
        setOutput((o) => {
          const last = o[o.length - 1];
          return last?.stream === stream ? [...o.slice(0, -1), { stream, text: last.text + text }] : [...o, { stream, text }];
        }),
    };
    const { result, cancel } = lesson.capabilities.multi_file
      ? engine.submitFilesStreaming(courseId, lessonId, JSON.parse(codeRef.current).files, handlers)
      : engine.submitStreaming(courseId, lessonId, codeRef.current, handlers);
    cancelRef.current = cancel;
    try {
      const g = await result;
      setGrade(g);
      telemetry.current?.submission(classifyGrade(g));
      setSaveState("saved");
      refreshProgress();
    } catch (e) {
      if (!String(e).includes("cancelled")) setRunError(String(e));
    } finally {
      cancelRef.current = undefined;
      setRunning(false);
    }
  }, [lesson, courseId, lessonId, refreshProgress, flushSave]);

  // Replay: advance about 20 frames a second.
  const frameCount = simResult?.timeline.frames.length ?? 0;
  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => setFrame((f) => Math.min(f + 1, frameCount - 1)), 50);
    return () => window.clearInterval(id);
  }, [playing, frameCount]);
  useEffect(() => {
    if (playing && frame >= frameCount - 1) setPlaying(false);
  }, [playing, frame, frameCount]);

  // Changing the chaos setup re-runs the simulation right away (debounced,
  // so toggling several targets quickly runs once).
  const submitRef = useRef(submit);
  submitRef.current = submit;
  const chaosTimer = useRef<number>(undefined);
  const changeChaos = (c: engine.Chaos) => {
    chaosRef.current = c;
    setChaos(c);
    window.clearTimeout(chaosTimer.current);
    chaosTimer.current = window.setTimeout(() => void submitRef.current(), 250);
  };
  useEffect(() => () => window.clearTimeout(chaosTimer.current), [lessonId]);

  // ⌘/Ctrl+Enter anywhere (Monaco handles it itself while focused).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && !e.defaultPrevented && !scratchpadOpen) {
        e.preventDefault();
        submit();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [submit, scratchpadOpen]);

  const markComplete = async () => {
    setMarking(true);
    setRunError(undefined);
    try {
      await engine.completeArticle(courseId, lessonId);
      telemetry.current?.submission("pass");
      refreshProgress();
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setMarking(false);
    }
  };

  const submitAnswers = async (answers: number[]) => {
    const res = await engine.submitAnswers(courseId, lessonId, answers);
    telemetry.current?.submission(res.passed ? "pass" : "failed_assertion");
    refreshProgress();
    return res;
  };

  const checkAnswer = async (question: number, answer: number) => {
    const res = await engine.checkAnswer(courseId, lessonId, question, answer);
    telemetry.current?.run();
    return res;
  };

  // --- multi-file workspace ---
  const readOnlyFiles = new Set((lesson?.files ?? []).filter((f) => f.readOnly).map((f) => f.path));
  const openFile = (path: string) => {
    setActiveFile(path);
    setOpenTabs((tabs) => (tabs.includes(path) ? tabs : [...tabs, path]));
  };
  const closeTab = (path: string) => {
    setOpenTabs((tabs) => {
      const rest = tabs.filter((t) => t !== path);
      if (path === activeFile && rest.length) setActiveFile(rest[Math.max(0, tabs.indexOf(path) - 1)]);
      return rest.length ? rest : tabs; // keep at least one tab open
    });
  };
  const onFileChange = (path: string, value: string) => {
    if (!lesson || readOnlyFiles.has(path)) return;
    filesRef.current = { ...filesRef.current, [path]: value };
    setFiles(filesRef.current);
    onCodeChange(editableFilesJSON(lesson, filesRef.current));
  };

  const reset = async () => {
    if (!lesson) return;
    window.clearTimeout(timer.current);
    pending.current = null;
    setConfirmReset(false);
    codeRef.current = lesson.starter;
    if (lesson.capabilities.multi_file && lesson.files?.length) {
      filesRef.current = Object.fromEntries(lesson.files.map((f) => [f.path, f.content]));
      setFiles(filesRef.current);
      codeRef.current = editableFilesJSON(lesson, filesRef.current);
    }
    setCode(codeRef.current);
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
          {caps?.scratchpad && (
            <button
              onClick={() => setScratchpadOpen(true)}
              title="Open the scratchpad to try code freely"
              className="flex items-center gap-1.5 rounded px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
            >
              <span className="font-mono text-[11px] text-indigo-300">&gt;_</span> Scratchpad
            </button>
          )}
          {caps?.telemetry && lesson && (
            <InsightsButton
              courseId={courseId}
              lessonId={lesson.id}
              flush={async () => {
                await telemetry.current?.flush();
              }}
              onAllowedChange={setTelemetryOn}
              onCleared={() => {
                telemetry.current?.discard();
                setTelemetryEpoch((e) => e + 1);
              }}
            />
          )}
          {(caps?.scratchpad || caps?.telemetry) && <span className="mx-1 h-4 w-px bg-zinc-800" />}
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
              questions={lesson.questions ?? []}
              initialAnswers={quizAnswers}
              completed={completed}
              onSubmit={submitAnswers}
              onCheck={lesson.immediateFeedback ? checkAnswer : undefined}
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
                      {isDesign ? "architecture" : multiFile ? `${lesson?.files?.length ?? 0} files` : `solution.${extension(lesson?.language)}`}
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
                        {isDesign
                          ? running
                            ? "Simulating…"
                            : chaos.nodes.length + chaos.edges.length > 0
                              ? "⚡ Run experiment"
                              : lesson?.simulation?.kind === "fencing"
                                ? "▶ Run Scenario"
                                : "▶ Simulate Traffic"
                          : running
                            ? "Running…"
                            : "▶ Run tests"}
                      </button>
                    </div>
                  </div>
                  <div className="min-h-0 flex-1">
                    {lesson && isDesign && (
                      <div className="flex h-full flex-col">
                        <div className="min-h-0 flex-1">
                          <SystemCanvas
                            key={`${courseId}/${lessonId}/${canvasKey}`}
                            initial={code}
                            onChange={onCodeChange}
                            result={simStale ? undefined : simResult}
                            frame={simResult && !simStale && !running ? simResult.timeline.frames[frame] : undefined}
                            running={running}
                            budget={lesson.maxBudget}
                            chaos={chaos}
                            onChaosChange={changeChaos}
                            scenario={lesson.simulation}
                          />
                        </div>
                        {simResult && !simStale && !running && (
                          <TimelineScrubber
                            timeline={simResult.timeline}
                            frame={Math.min(frame, frameCount - 1)}
                            onFrame={(f) => {
                              setPlaying(false);
                              setFrame(f);
                            }}
                            playing={playing}
                            onTogglePlay={() => {
                              if (!playing && frame >= frameCount - 1) setFrame(0);
                              setPlaying((p) => !p);
                            }}
                          />
                        )}
                      </div>
                    )}
                    {lesson && multiFile && (
                      <div className="flex h-full">
                        <nav className="w-48 shrink-0 overflow-auto border-r border-zinc-800 bg-zinc-950" aria-label="Files">
                          <div className="px-3 pt-2 pb-1 text-[10px] font-medium tracking-wide text-zinc-500 uppercase">Files</div>
                          <FileTree files={lesson.files ?? []} active={activeFile} onOpen={openFile} />
                        </nav>
                        <div className="flex min-w-0 flex-1 flex-col">
                          <div className="flex h-8 shrink-0 items-end overflow-x-auto border-b border-zinc-800 bg-zinc-950 text-xs" role="tablist">
                            {openTabs.map((path) => (
                              <div
                                key={path}
                                role="tab"
                                aria-selected={path === activeFile}
                                className={`group flex h-full shrink-0 items-center gap-1.5 border-r border-zinc-800 pr-1 pl-3 ${
                                  path === activeFile ? "bg-[#0b0b0e] text-zinc-100" : "text-zinc-500 hover:text-zinc-300"
                                }`}
                              >
                                <button onClick={() => setActiveFile(path)} title={path} className="flex items-center gap-1.5">
                                  {path.split("/").pop()}
                                  {readOnlyFiles.has(path) && <LockIcon />}
                                </button>
                                <button
                                  onClick={() => closeTab(path)}
                                  aria-label={`Close ${path}`}
                                  disabled={openTabs.length === 1}
                                  className="rounded px-1 text-zinc-600 opacity-0 group-hover:opacity-100 hover:bg-zinc-800 hover:text-zinc-200 disabled:hidden"
                                >
                                  ✕
                                </button>
                              </div>
                            ))}
                            {readOnlyFiles.has(activeFile) && (
                              <span className="mb-1.5 ml-auto shrink-0 pr-3 text-[11px] text-amber-400/80">Read-only helper file</span>
                            )}
                          </div>
                          <div className="min-h-0 flex-1">
                            <CodeEditor
                              path={`${courseId}/${lessonId}/${activeFile}`}
                              language={languageForPath(activeFile)}
                              value={files[activeFile] ?? ""}
                              onChange={(v) => onFileChange(activeFile, v)}
                              onSubmit={submit}
                              readOnly={readOnlyFiles.has(activeFile)}
                            />
                          </div>
                        </div>
                      </div>
                    )}
                    {lesson && !isDesign && !multiFile && (
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
                    scenario={lesson?.simulation}
                    stale={simStale && !!simResult}
                    onNext={next ? () => onOpenLesson(next.id) : undefined}
                    onSeek={(ms) => {
                      if (!simResult) return;
                      setPlaying(false);
                      setFrame(Math.min(frameCount - 1, Math.floor(ms / simResult.timeline.intervalMs)));
                    }}
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
      {caps?.scratchpad && (
        <ScratchpadModal
          open={scratchpadOpen}
          onClose={() => setScratchpadOpen(false)}
          onRun={() => telemetry.current?.run()}
          defaultLanguage={lesson?.language}
          lessonFiles={lesson?.kind !== "code" ? undefined : multiFile ? files : { [`solution.${extension(lesson.language)}`]: code }}
        />
      )}
    </div>
  );
}

/** A multi-file lesson's files with the learner's saved edits applied. */
function restoreFiles(l: engine.Lesson, saved: string | null): Record<string, string> {
  const files = Object.fromEntries((l.files ?? []).map((f) => [f.path, f.content]));
  let edits: Record<string, string> | undefined;
  try {
    const parsed = saved ? JSON.parse(saved) : undefined;
    if (parsed && typeof parsed.files === "object") edits = parsed.files;
  } catch {
    // Saved before the lesson became multi-file: plain code for solution.<ext>.
    const solution = l.files?.find((f) => f.path.startsWith("solution."));
    if (saved && solution) edits = { [solution.path]: saved };
  }
  for (const f of l.files ?? []) {
    if (!f.readOnly && edits && typeof edits[f.path] === "string") files[f.path] = edits[f.path];
  }
  return files;
}

/** What's saved and submitted for a multi-file lesson: the editable files. */
function editableFilesJSON(l: engine.Lesson, files: Record<string, string>): string {
  const editable = (l.files ?? []).filter((f) => !f.readOnly).map((f) => [f.path, files[f.path] ?? f.content]);
  return JSON.stringify({ files: Object.fromEntries(editable) });
}

function parseQuizAnswers(saved: string | null): number[] | undefined {
  try {
    const parsed = saved ? JSON.parse(saved) : undefined;
    if (Array.isArray(parsed?.answers)) return parsed.answers;
    if (typeof parsed?.answer === "number") return [parsed.answer]; // older single-answer saves
  } catch {
    // not saved, or not JSON
  }
  return undefined;
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
