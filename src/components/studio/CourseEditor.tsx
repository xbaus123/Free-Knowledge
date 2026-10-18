import { useCallback, useEffect, useRef, useState } from "react";
import * as engine from "../../lib/engine";
import * as studio from "../../lib/studio";
import { CodeEditor } from "../CodeEditor";
import { SystemCanvas } from "../design/SystemCanvas";
import { Markdown } from "../Markdown";
import { TestList } from "../OutputPanel";
import { MultiFileEditor } from "./MultiFileEditor";
import { QuizBuilder } from "./QuizBuilder";
import { Field, inputClass } from "./StudioHome";
import { extension, LANGUAGES } from "./languages";

interface Props {
  courseId: string;
  initialLessonId?: string;
  onBack: () => void;
  onPreview: (courseId: string, lessonId: string) => void;
}

type Tab = "instructions" | "starter" | "tests" | "reference" | "questions" | "starterDiagram" | "solutionDiagram" | "simulation";

type TabInfo = { id: Tab; label: string; hint: string; code?: boolean };

/** The editing tabs for each lesson type. */
function tabsFor(type: studio.LessonType): TabInfo[] {
  switch (type) {
    case "article":
      return [{ id: "instructions", label: "Article", hint: "lesson.md: learners read this, then click Mark Complete" }];
    case "quiz":
      return [
        { id: "instructions", label: "Intro", hint: "lesson.md: shown beside the questions" },
        { id: "questions", label: "Questions", hint: "Questions, options, and answers (answers stay hidden from learners)" },
      ];
    case "system-design":
      return [
        { id: "instructions", label: "Instructions", hint: "lesson.md: the scenario and the goal" },
        { id: "starterDiagram", label: "Starter diagram", hint: "starter.json: the architecture learners start from" },
        { id: "solutionDiagram", label: "Solution diagram", hint: "solution.json: a design that must pass the simulation" },
        { id: "simulation", label: "Simulation", hint: "Traffic, faults, goals, and which nodes the canvas offers (the \"simulation\" object in config.json)" },
      ];
    default:
      return [
        { id: "instructions", label: "Instructions", hint: "lesson.md: what the learner reads" },
        { id: "starter", label: "Starter", hint: "The code learners start with", code: true },
        { id: "tests", label: "Tests", hint: "Hidden tests. The learner's code is saved as solution.<ext> next to them", code: true },
        { id: "reference", label: "Reference", hint: "Your solution. It must pass the tests before you can export", code: true },
      ];
  }
}

const TYPE_LABELS: Record<studio.LessonType, string> = { code: "Code", article: "Article", quiz: "Quiz", "system-design": "System design" };

const CHECK_HINTS: Record<studio.LessonType, string> = {
  code: "Runs your reference solution and the starter against the tests (⌘ Enter)",
  article: "Checks that the lesson loads (⌘ Enter)",
  quiz: "Checks that every question has options and a correct answer (⌘ Enter)",
  "system-design": "Simulates the solution diagram (must pass) and the starter (should fail) (⌘ Enter)",
};

const codeField = (tab: Tab) => (tab === "instructions" ? "markdown" : (tab as "starter" | "tests" | "reference"));

export function CourseEditor({ courseId, initialLessonId, onBack, onPreview }: Props) {
  const [course, setCourse] = useState<engine.Course>();
  const [meta, setMeta] = useState<studio.CourseMeta>({ title: "", description: "", author: "", version: "" });
  const [showSettings, setShowSettings] = useState(false);
  const [lessonId, setLessonId] = useState(initialLessonId);
  const [draft, setDraft] = useState<studio.LessonSource>();
  const [saved, setSaved] = useState<studio.LessonSource>();
  const [tab, setTab] = useState<Tab>("instructions");
  const [check, setCheck] = useState<studio.LessonCheckDetail>();
  const [checks, setChecks] = useState<Record<string, studio.LessonCheck>>({});
  const [busy, setBusy] = useState<string>();
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();
  const [adding, setAdding] = useState(false);
  const [showCaps, setShowCaps] = useState(false);

  // Latest draft for save-before-navigate/check/export. Updated synchronously
  // in `update`, since a click can land before React re-renders after typing.
  const draftRef = useRef(draft);
  draftRef.current = draft;
  const savedRef = useRef(saved);
  savedRef.current = saved;
  const dirty = !!draft && JSON.stringify(draft) !== JSON.stringify(saved);

  const loadCourse = useCallback(async () => {
    const c = await engine.course(courseId);
    setCourse(c);
    setMeta({ title: c.title, description: c.description, author: c.author ?? "", version: c.version ?? "", language: c.language });
    return c;
  }, [courseId]);

  useEffect(() => {
    loadCourse()
      .then((c) => setLessonId((id) => id ?? c.lessons[0]?.id))
      .catch((e) => setError(String(e)));
  }, [loadCourse]);

  useEffect(() => {
    if (!lessonId) {
      setDraft(undefined);
      setSaved(undefined);
      return;
    }
    let stale = false;
    setCheck(undefined);
    studio.lessonSource(courseId, lessonId).then(
      (src) => {
        if (stale) return;
        setDraft(src);
        setSaved(src);
      },
      (e) => !stale && setError(String(e)),
    );
    return () => {
      stale = true;
    };
  }, [courseId, lessonId]);

  const act = async (label: string, fn: () => Promise<void>) => {
    setBusy(label);
    setError(undefined);
    setNotice(undefined);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(undefined);
    }
  };

  /** Saves the current lesson if it has unsaved changes. */
  const saveDraft = useCallback(async () => {
    const d = draftRef.current;
    if (!d || JSON.stringify(d) === JSON.stringify(savedRef.current)) return;
    await studio.saveLesson(courseId, d);
    setSaved(d);
    await loadCourse(); // titles and problems may have changed
  }, [courseId, loadCourse]);

  const save = () => act("save", saveDraft);

  const runCheck = () =>
    act("check", async () => {
      if (!lessonId) return;
      await saveDraft();
      const d = await studio.checkLesson(courseId, lessonId);
      setCheck(d);
      setChecks((c) => ({ ...c, [d.lessonId]: d }));
    });

  const selectLesson = (id: string) =>
    act("navigate", async () => {
      await saveDraft();
      setLessonId(id);
    });

  const move = (id: string, delta: number) =>
    act("reorder", async () => {
      if (!course) return;
      const order = course.lessons.map((l) => l.id);
      const i = order.indexOf(id);
      const j = i + delta;
      if (j < 0 || j >= order.length) return;
      [order[i], order[j]] = [order[j], order[i]];
      await studio.updateCourse(courseId, meta, order);
      await loadCourse();
    });

  const deleteCurrent = () =>
    act("delete", async () => {
      if (!course || !draft) return;
      if (!(await studio.confirmDialog(`Delete the lesson "${draft.title}"? This can't be undone.`))) return;
      const i = course.lessons.findIndex((l) => l.id === draft.id);
      await studio.deleteLesson(courseId, draft.id);
      const c = await loadCourse();
      setLessonId(c.lessons[Math.min(i, c.lessons.length - 1)]?.id);
    });

  const addLesson = (title: string, type: studio.LessonType, language: string) =>
    act("add", async () => {
      await saveDraft();
      const { id } = await studio.createLesson(courseId, title, type, type === "code" ? language : undefined);
      await loadCourse();
      setLessonId(id);
      setTab("instructions");
      setAdding(false);
    });

  const saveMeta = () =>
    act("settings", async () => {
      await studio.updateCourse(courseId, meta);
      await loadCourse();
      setShowSettings(false);
    });

  const doExport = () =>
    act("export", async () => {
      await saveDraft();
      setCheck(undefined); // the per-lesson marks in the list replace it
      const path = await studio.pickDojoToSave(`${courseId}.dojo`);
      if (!path) return;
      try {
        const res = await studio.exportCourse(courseId, path);
        setChecks(Object.fromEntries(res.checks.map((c) => [c.lessonId, c])));
        const warnings = res.checks.filter((c) => c.warning).length;
        setNotice(`Exported to ${res.path}${warnings ? ` (${warnings} lesson${warnings > 1 ? "s have" : " has"} warnings)` : ""}.`);
      } catch (e) {
        if (e instanceof engine.EngineError && Array.isArray(e.body.checks)) {
          const list = e.body.checks as studio.LessonCheck[];
          setChecks(Object.fromEntries(list.map((c) => [c.lessonId, c])));
          const failing = list.filter((c) => !c.ok);
          throw new Error(
            `Can't export yet: ${failing.length} lesson${failing.length > 1 ? "s" : ""} failed validation (${failing.map((c) => c.title).join(", ")}). They're marked ✗ in the list.`,
          );
        }
        throw e;
      }
    });

  const preview = () =>
    act("preview", async () => {
      if (!lessonId) return;
      await saveDraft();
      onPreview(courseId, lessonId);
    });

  const back = () => act("back", async () => (await saveDraft(), onBack()));

  // ⌘S saves, ⌘Enter checks (Monaco handles these itself while focused).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey) || e.defaultPrevented) return;
      if (e.key === "s") {
        e.preventDefault();
        save();
      } else if (e.key === "Enter") {
        e.preventDefault();
        runCheck();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const update = (patch: Partial<studio.LessonSource>) => {
    if (!draftRef.current) return;
    draftRef.current = { ...draftRef.current, ...patch };
    setDraft(draftRef.current);
  };
  const ext = extension(draft?.language);
  const caps: engine.Capabilities = draft?.capabilities ?? { scratchpad: false, multi_file: false, telemetry: false };
  const multi = draft?.type === "code" && caps.multi_file;

  const setCapability = (key: "scratchpad" | "multi_file" | "telemetry", on: boolean) => {
    if (!draft) return;
    const solution = `solution.${ext}`;
    const patch: Partial<studio.LessonSource> = { capabilities: { ...caps, [key]: on } };
    if (key === "multi_file" && on && !Object.keys(draft.starterFiles ?? {}).length) {
      // Start the file tree from the single-file lesson.
      patch.starterFiles = { [solution]: draft.starter };
      patch.referenceFiles = { [solution]: draft.reference };
    }
    if (key === "multi_file" && !on) {
      // Back to one file: keep the solution file's contents.
      patch.starter = draft.starterFiles?.[solution] ?? draft.starter;
      patch.reference = draft.referenceFiles?.[solution] ?? draft.reference;
      patch.capabilities = { ...caps, multi_file: false, read_only_files: [] };
    }
    update(patch);
  };
  const enabledCaps = [caps.scratchpad && "Scratchpad", multi && "Multi-file", caps.telemetry && "Insights"].filter(Boolean);
  const tabs = draft ? tabsFor(draft.type) : [];
  const activeTab = tabs.some((t) => t.id === tab) ? tab : "instructions";

  return (
    <div className="flex h-full flex-col">
      <header className="flex h-11 shrink-0 items-center gap-3 border-b border-zinc-800 bg-zinc-950 px-3 text-sm">
        <button onClick={back} className="rounded px-2 py-1 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
          ← Studio
        </button>
        <span className="truncate font-medium">{course?.title}</span>
        <button onClick={() => setShowSettings((s) => !s)} className="rounded px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
          Course settings
        </button>
        <div className="ml-auto flex items-center gap-2">
          {busy && <span className="text-xs text-zinc-500">{busy === "export" ? "Checking every lesson…" : busy === "check" ? "Checking…" : "Working…"}</span>}
          <button onClick={preview} disabled={!lessonId || !!busy} className="rounded px-2.5 py-1 text-zinc-300 hover:bg-zinc-800 disabled:opacity-40">
            Preview as learner
          </button>
          <button
            onClick={doExport}
            disabled={!course?.lessons.length || !!busy}
            className="rounded bg-indigo-600 px-3 py-1 font-medium hover:bg-indigo-500 disabled:opacity-40"
          >
            Export .dojo
          </button>
        </div>
      </header>

      {error && <p className="border-b border-red-900 bg-red-950/50 px-4 py-2 text-sm text-red-300">{error}</p>}
      {notice && <p className="border-b border-emerald-900 bg-emerald-950/50 px-4 py-2 text-sm text-emerald-300">{notice}</p>}

      {showSettings && (
        <div className="grid shrink-0 gap-3 border-b border-zinc-800 bg-zinc-900/60 p-4 sm:grid-cols-4">
          <Field label="Title">
            <input value={meta.title} onChange={(e) => setMeta({ ...meta, title: e.target.value })} className={inputClass} />
          </Field>
          <Field label="Author">
            <input value={meta.author} onChange={(e) => setMeta({ ...meta, author: e.target.value })} className={inputClass} />
          </Field>
          <Field label="Version">
            <input value={meta.version} onChange={(e) => setMeta({ ...meta, version: e.target.value })} className={inputClass} />
          </Field>
          <Field label="Default language">
            <select value={meta.language ?? ""} onChange={(e) => setMeta({ ...meta, language: e.target.value || undefined })} className={inputClass}>
              <option value="">None</option>
              {LANGUAGES.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </Field>
          <div className="sm:col-span-3">
            <Field label="Description">
              <input value={meta.description} onChange={(e) => setMeta({ ...meta, description: e.target.value })} className={inputClass} />
            </Field>
          </div>
          <div className="flex items-end justify-end gap-2">
            <button onClick={() => setShowSettings(false)} className="rounded px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800">
              Cancel
            </button>
            <button onClick={saveMeta} disabled={!meta.title.trim()} className="rounded bg-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-600 disabled:opacity-40">
              Save settings
            </button>
          </div>
        </div>
      )}

      <div className="flex min-h-0 flex-1">
        <aside className="flex w-64 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
          <div className="px-3 pt-3 pb-1 text-xs font-medium tracking-wide text-zinc-500 uppercase">Lessons</div>
          <ol className="min-h-0 flex-1 overflow-auto px-2 text-sm">
            {course?.lessons.map((l, i) => {
              const c = checks[l.id];
              return (
                <li key={l.id} className="group flex items-center">
                  <button
                    onClick={() => l.id !== lessonId && selectLesson(l.id)}
                    className={`flex min-w-0 flex-1 items-center gap-2 rounded px-2 py-1.5 text-left ${
                      l.id === lessonId ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
                    }`}
                    title={c?.problem ?? c?.warning ?? l.problems?.join("\n")}
                  >
                    <span
                      className={`w-4 shrink-0 text-center text-xs ${
                        c ? (c.ok ? (c.warning ? "text-amber-400" : "text-emerald-400") : "text-red-400") : l.problems?.length ? "text-amber-400" : "text-zinc-600"
                      }`}
                    >
                      {c ? (c.ok ? (c.warning ? "!" : "✓") : "✗") : l.problems?.length ? "!" : i + 1}
                    </span>
                    <span className="truncate">{l.title}</span>
                  </button>
                  <span className="flex shrink-0 opacity-0 group-hover:opacity-100 focus-within:opacity-100">
                    <IconButton label="Move up" disabled={i === 0 || !!busy} onClick={() => move(l.id, -1)}>
                      ↑
                    </IconButton>
                    <IconButton label="Move down" disabled={i === course.lessons.length - 1 || !!busy} onClick={() => move(l.id, 1)}>
                      ↓
                    </IconButton>
                  </span>
                </li>
              );
            })}
          </ol>
          <div className="border-t border-zinc-800 p-2">
            {adding ? (
              <NewLessonForm
                defaultLanguage={draft?.language || course?.language || "python"}
                onAdd={addLesson}
                onCancel={() => setAdding(false)}
              />
            ) : (
              <button onClick={() => setAdding(true)} className="w-full rounded px-2 py-1.5 text-left text-sm text-indigo-300 hover:bg-zinc-900">
                + Add lesson
              </button>
            )}
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col">
          {!draft ? (
            <div className="p-8 text-sm text-zinc-500">
              {course && course.lessons.length === 0 ? "Add your first lesson to get started." : "Loading…"}
            </div>
          ) : (
            <>
              <div className="flex shrink-0 flex-wrap items-end gap-3 border-b border-zinc-800 px-4 py-3">
                <label className="min-w-48 flex-1">
                  <span className="mb-1 flex items-center gap-2 text-xs text-zinc-400">
                    Lesson title
                    {draft.type !== "code" && (
                      <span className="rounded bg-violet-950 px-1.5 py-px text-[10px] text-violet-300">{TYPE_LABELS[draft.type]}</span>
                    )}
                  </span>
                  <input value={draft.title} onChange={(e) => update({ title: e.target.value })} className={inputClass} />
                </label>
                {draft.type === "code" && (
                  <>
                    <label>
                      <span className="mb-1 block text-xs text-zinc-400">Language</span>
                      <select
                        value={draft.language}
                        onChange={(e) => update({ language: e.target.value })}
                        className={inputClass}
                        title="Switching language keeps your code; update the files to match"
                      >
                        {LANGUAGES.map((l) => (
                          <option key={l.id} value={l.id}>
                            {l.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="w-28">
                      <span className="mb-1 block text-xs text-zinc-400">Time limit (s)</span>
                      <input
                        type="number"
                        min={1}
                        max={60}
                        placeholder="10"
                        value={draft.timeoutMs ? draft.timeoutMs / 1000 : ""}
                        onChange={(e) => update({ timeoutMs: e.target.value ? Math.round(Number(e.target.value) * 1000) : undefined })}
                        className={inputClass}
                      />
                    </label>
                  </>
                )}
                {draft.type === "system-design" && (
                  <label className="w-36">
                    <span className="mb-1 block text-xs text-zinc-400">Budget ($/month)</span>
                    <input
                      type="number"
                      min={1}
                      placeholder="none"
                      value={draft.maxBudget ?? ""}
                      onChange={(e) => update({ maxBudget: e.target.value ? Math.round(Number(e.target.value)) : undefined })}
                      className={inputClass}
                    />
                  </label>
                )}
                {draft.type === "system-design" && (
                  <label className="w-40">
                    <span className="mb-1 block text-xs text-zinc-400">p99 latency target (ms)</span>
                    <input
                      type="number"
                      min={1}
                      max={60000}
                      placeholder="none"
                      value={draft.maxLatencyMs ?? ""}
                      onChange={(e) => update({ maxLatencyMs: e.target.value ? Math.round(Number(e.target.value)) : undefined })}
                      className={inputClass}
                    />
                  </label>
                )}
                {draft.type === "quiz" && (
                  <label
                    className="flex cursor-pointer items-center gap-2 self-end pb-2 text-sm text-zinc-300"
                    title="Learners see whether each answer is right as soon as they pick it, instead of submitting all their answers at the end"
                  >
                    <input
                      type="checkbox"
                      checked={!!draft.immediateFeedback}
                      onChange={(e) => update({ immediateFeedback: e.target.checked || undefined })}
                      className="accent-indigo-500"
                    />
                    Check each answer immediately
                  </label>
                )}
                <div className="ml-auto flex items-center gap-2 text-sm">
                  <span className="text-xs text-zinc-500">{dirty ? "Unsaved changes" : "Saved"}</span>
                  <button onClick={deleteCurrent} disabled={!!busy} className="rounded px-2 py-1.5 text-xs text-zinc-500 hover:bg-zinc-800 hover:text-red-400">
                    Delete
                  </button>
                  <button onClick={save} disabled={!dirty || !!busy} title="⌘S" className="rounded bg-zinc-700 px-3 py-1.5 hover:bg-zinc-600 disabled:opacity-40">
                    Save
                  </button>
                  <button
                    onClick={runCheck}
                    disabled={!!busy}
                    title={CHECK_HINTS[draft.type]}
                    className="rounded bg-emerald-700 px-3 py-1.5 font-medium hover:bg-emerald-600 disabled:opacity-40"
                  >
                    Check lesson
                  </button>
                </div>
              </div>

              <div className="shrink-0 border-b border-zinc-800">
                <button
                  onClick={() => setShowCaps((v) => !v)}
                  aria-expanded={showCaps}
                  className="flex w-full items-center gap-2 px-4 py-2 text-left text-xs text-zinc-400 hover:bg-zinc-900/60"
                >
                  <span className="w-3 text-[10px]">{showCaps ? "▾" : "▸"}</span>
                  <span className="font-medium text-zinc-300">Lesson capabilities</span>
                  <span className="text-zinc-500">{enabledCaps.length ? enabledCaps.join(" · ") : "None enabled"}</span>
                </button>
                {showCaps && (
                  <div className="grid gap-3 px-4 pb-4 sm:grid-cols-3">
                    <CapabilityToggle
                      label="Scratchpad access"
                      description="Learners can open a free-form code runner from the lesson. It isn't graded."
                      checked={caps.scratchpad}
                      onChange={(on) => setCapability("scratchpad", on)}
                    />
                    <CapabilityToggle
                      label="Multi-file workspace"
                      description={
                        draft.type === "code"
                          ? "A file tree and tabs instead of one file. Add files and lock helpers in the Starter tab."
                          : "Only available for code exercises."
                      }
                      checked={multi}
                      disabled={draft.type !== "code"}
                      onChange={(on) => setCapability("multi_file", on)}
                    />
                    <CapabilityToggle
                      label="Telemetry & learning insights"
                      description="Records reading and typing time, attempts, and error types on the learner's device. Learners can turn it off."
                      checked={caps.telemetry}
                      onChange={(on) => setCapability("telemetry", on)}
                    />
                  </div>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-1 border-b border-zinc-800 px-2 text-xs">
                {tabs.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    className={`border-b-2 px-3 py-2 ${activeTab === t.id ? "border-indigo-500 text-zinc-100" : "border-transparent text-zinc-400 hover:text-zinc-200"}`}
                  >
                    {t.label}
                    {t.code && <span className="ml-1 font-mono text-zinc-500">{multi && t.id !== "tests" ? "files" : `.${ext}`}</span>}
                  </button>
                ))}
                <span className="ml-auto truncate pr-2 text-zinc-500">{tabs.find((t) => t.id === activeTab)?.hint}</span>
              </div>

              <div className="flex min-h-0 flex-1">
                {multi && (activeTab === "starter" || activeTab === "reference") ? (
                  <MultiFileEditor
                    key={`${draft.id}/${activeTab}`}
                    mode={activeTab}
                    idPrefix={`${courseId}/${draft.id}`}
                    starterFiles={draft.starterFiles ?? {}}
                    referenceFiles={draft.referenceFiles ?? {}}
                    readOnly={caps.read_only_files ?? []}
                    ext={ext}
                    onChange={({ starterFiles, referenceFiles, readOnly }) =>
                      update({ starterFiles, referenceFiles, capabilities: { ...caps, read_only_files: readOnly } })
                    }
                    onSave={save}
                    onSubmit={runCheck}
                  />
                ) : activeTab === "questions" ? (
                  <div className="w-full">
                    <QuizBuilder questions={draft.questions ?? []} onChange={(questions) => update({ questions })} />
                  </div>
                ) : activeTab === "starterDiagram" || activeTab === "solutionDiagram" ? (
                  <div className="w-full">
                    <SystemCanvas
                      key={`${draft.id}/${activeTab}`}
                      initial={activeTab === "starterDiagram" ? draft.starter : draft.reference}
                      onChange={(json) => update(activeTab === "starterDiagram" ? { starter: json } : { reference: json })}
                      result={activeTab === "starterDiagram" ? check?.starterSim : check?.referenceSim}
                      budget={draft.maxBudget}
                      scenario={draft.simulation}
                    />
                  </div>
                ) : activeTab === "simulation" ? (
                  <SimulationSettings
                    key={draft.id}
                    path={`studio/${courseId}/${draft.id}/simulation.json`}
                    value={draft.simulation}
                    onChange={(simulation) => update({ simulation })}
                    onSave={save}
                    onSubmit={runCheck}
                  />
                ) : (
                  <>
                    <div className={activeTab === "instructions" ? "w-1/2 border-r border-zinc-800" : "w-full"}>
                      <CodeEditor
                        path={`studio/${courseId}/${draft.id}/${activeTab}.${activeTab === "instructions" ? "md" : ext}`}
                        language={activeTab === "instructions" ? "markdown" : (draft.language ?? "")}
                        value={draft[codeField(activeTab)]}
                        onChange={(v) => update({ [codeField(activeTab)]: v })}
                        onSave={save}
                        onSubmit={runCheck}
                        autoFocus={false}
                      />
                    </div>
                    {activeTab === "instructions" && (
                      <div className="w-1/2 overflow-auto px-6 py-5">
                        <Markdown>{draft.markdown}</Markdown>
                      </div>
                    )}
                  </>
                )}
              </div>

              {check && <CheckPanel check={check} onClose={() => setCheck(undefined)} />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

const SIMULATION_EXAMPLE = `{
  "palette": ["client", "loadBalancer", "server", "cache", "database"],
  "traffic": { "requests": 2000, "mix": { "read": 80, "write": 20 }, "read_your_writes_ms": 30 },
  "faults": [{ "kind": "crash", "type": "server", "at_ms": 500 }],
  "goals": { "max_stale_pct": 1, "max_failed_pct": 5 }
}`;

/** Edits the scenario as JSON; the engine validates it on save. */
function SimulationSettings({
  path,
  value,
  onChange,
  onSave,
  onSubmit,
}: {
  path: string;
  value?: engine.SimulationConfig;
  onChange: (v: engine.SimulationConfig | undefined) => void;
  onSave: () => void;
  onSubmit: () => void;
}) {
  const [text, setText] = useState(() => (value && Object.keys(value).length ? JSON.stringify(value, null, 2) : ""));
  const [error, setError] = useState<string>();
  return (
    <div className="flex w-full flex-col">
      <div className="min-h-0 flex-1">
        <CodeEditor
          path={path}
          language="javascript"
          value={text}
          onChange={(v) => {
            setText(v);
            if (!v.trim()) {
              setError(undefined);
              onChange(undefined);
              return;
            }
            try {
              const parsed = JSON.parse(v);
              if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new Error("must be a JSON object");
              setError(undefined);
              onChange(parsed);
            } catch (e) {
              setError(e instanceof Error ? e.message : String(e));
            }
          }}
          onSave={onSave}
          onSubmit={onSubmit}
          autoFocus={false}
        />
      </div>
      <div className="shrink-0 border-t border-zinc-800 px-4 py-2 text-xs text-zinc-400">
        {error ? (
          <span className="text-red-400">Invalid JSON: {error}</span>
        ) : (
          <>
            Leave empty for the default: 1,000 reads in one second with no faults. Example:{" "}
            <code className="font-mono text-zinc-300">{SIMULATION_EXAMPLE.replace(/\s+/g, " ")}</code>
          </>
        )}
      </div>
    </div>
  );
}

function CheckPanel({ check, onClose }: { check: studio.LessonCheckDetail; onClose: () => void }) {
  return (
    <section className="max-h-72 shrink-0 overflow-auto border-t border-zinc-800 bg-zinc-950 p-4 text-sm">
      <div className="mb-3 flex items-center gap-3">
        <span className={`font-medium ${check.ok ? (check.warning ? "text-amber-300" : "text-emerald-300") : "text-red-400"}`}>
          {check.ok ? (check.warning ? "Ready to export, with a warning" : "Ready to export") : "Needs fixing"}
        </span>
        <button onClick={onClose} className="ml-auto rounded px-2 py-0.5 text-xs text-zinc-500 hover:bg-zinc-800">
          Close
        </button>
      </div>
      {check.problem && <p className="mb-3 text-red-300">{check.problem}</p>}
      {check.warning && <p className="mb-3 text-amber-300">{check.warning}</p>}
      <div className="grid gap-6 md:grid-cols-2">
        {check.reference && <RunSummary title="Reference solution (should pass)" result={check.reference} expectPass />}
        {check.starter && <RunSummary title="Starter code (should fail)" result={check.starter} expectPass={false} />}
        {check.referenceSim && <SimSummary title="solution.json (should pass)" result={check.referenceSim} expectPass />}
        {check.starterSim && <SimSummary title="starter.json (should fail)" result={check.starterSim} expectPass={false} />}
      </div>
    </section>
  );
}

function RunSummary({ title, result, expectPass }: { title: string; result: engine.GradeResult; expectPass: boolean }) {
  const good = result.passed === expectPass;
  const passed = result.tests.filter((t) => t.status === "pass").length;
  return (
    <div>
      <h4 className="mb-2 text-xs font-medium tracking-wide text-zinc-400 uppercase">
        <span className={good ? "text-emerald-400" : "text-red-400"}>{good ? "✓" : "✗"}</span> {title}
      </h4>
      {result.phase === "compile" ? (
        <pre className="overflow-auto rounded bg-zinc-900 p-2 font-mono text-xs whitespace-pre-wrap text-red-200">{result.stderr || "compile failed"}</pre>
      ) : result.error ? (
        <p className="text-red-300">{result.error}</p>
      ) : result.tests.length === 0 ? (
        <pre className="overflow-auto rounded bg-zinc-900 p-2 font-mono text-xs whitespace-pre-wrap text-red-200">
          {result.timedOut ? "Timed out." : result.stderr || "No tests ran."}
        </pre>
      ) : (
        <>
          <p className="mb-2 text-xs text-zinc-500">
            {passed}/{result.tests.length} tests passed{result.timedOut ? " (timed out)" : ""}
          </p>
          <TestList tests={result.tests} />
        </>
      )}
    </div>
  );
}

function SimSummary({ title, result, expectPass }: { title: string; result: engine.SimResult; expectPass: boolean }) {
  const good = result.passed === expectPass;
  return (
    <div>
      <h4 className="mb-2 text-xs font-medium tracking-wide text-zinc-400 uppercase">
        <span className={good ? "text-emerald-400" : "text-red-400"}>{good ? "✓" : "✗"}</span> {title}
      </h4>
      <p className={result.passed ? "text-emerald-300" : "text-zinc-300"}>{result.message}</p>
      <p className="mt-1 text-xs text-zinc-500">
        p99 {result.metrics.p99Ms} ms · {result.metrics.completed.toLocaleString()}/{result.metrics.requests.toLocaleString()} answered
      </p>
    </div>
  );
}

function CapabilityToggle({
  label,
  description,
  checked,
  disabled,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (on: boolean) => void;
}) {
  return (
    <label className={`flex gap-3 rounded-lg border border-zinc-800 bg-zinc-900/40 p-3 ${disabled ? "opacity-50" : "cursor-pointer hover:border-zinc-700"}`}>
      <span className="relative mt-0.5 inline-flex shrink-0">
        <input
          type="checkbox"
          role="switch"
          aria-label={label}
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange(e.target.checked)}
          className="peer sr-only"
        />
        <span className="h-5 w-9 rounded-full bg-zinc-700 transition-colors peer-checked:bg-indigo-600 peer-focus-visible:ring-2 peer-focus-visible:ring-indigo-400" />
        <span className="absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white transition-transform peer-checked:translate-x-4" />
      </span>
      <span>
        <span className="block text-sm font-medium text-zinc-200">{label}</span>
        <span className="block text-xs text-zinc-500">{description}</span>
      </span>
    </label>
  );
}

function NewLessonForm({
  defaultLanguage,
  onAdd,
  onCancel,
}: {
  defaultLanguage: string;
  onAdd: (title: string, type: studio.LessonType, language: string) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [type, setType] = useState<studio.LessonType>("code");
  const [language, setLanguage] = useState(defaultLanguage);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (title.trim()) onAdd(title.trim(), type, language);
      }}
      className="space-y-2"
    >
      <input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Lesson title" className={inputClass} />
      <select value={type} onChange={(e) => setType(e.target.value as studio.LessonType)} className={inputClass} aria-label="Lesson type">
        <option value="code">Code exercise</option>
        <option value="article">Article (reading)</option>
        <option value="quiz">Quiz</option>
        <option value="system-design">System design</option>
      </select>
      {type === "code" && (
        <select value={language} onChange={(e) => setLanguage(e.target.value)} className={inputClass} aria-label="Language">
          {LANGUAGES.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </select>
      )}
      <div className="flex justify-end gap-1">
        <button type="button" onClick={onCancel} className="rounded px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800">
          Cancel
        </button>
        <button type="submit" disabled={!title.trim()} className="rounded bg-indigo-600 px-2.5 py-1 text-xs font-medium hover:bg-indigo-500 disabled:opacity-40">
          Add
        </button>
      </div>
    </form>
  );
}

function IconButton({ label, disabled, onClick, children }: { label: string; disabled: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className="rounded px-1.5 py-1 text-xs text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200 disabled:invisible"
    >
      {children}
    </button>
  );
}
