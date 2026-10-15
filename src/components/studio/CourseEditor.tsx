import { useCallback, useEffect, useRef, useState } from "react";
import * as engine from "../../lib/engine";
import * as studio from "../../lib/studio";
import { CodeEditor } from "../CodeEditor";
import { Markdown } from "../Markdown";
import { TestList } from "../OutputPanel";
import { Field, inputClass } from "./StudioHome";
import { extension, LANGUAGES } from "./languages";

interface Props {
  courseId: string;
  initialLessonId?: string;
  onBack: () => void;
  onPreview: (courseId: string, lessonId: string) => void;
}

type Tab = "instructions" | "starter" | "tests" | "reference";

const TABS: { id: Tab; label: string; hint: string }[] = [
  { id: "instructions", label: "Instructions", hint: "lesson.md: what the learner reads" },
  { id: "starter", label: "Starter", hint: "The code learners start with" },
  { id: "tests", label: "Tests", hint: "Hidden tests. The learner's code is saved as solution.<ext> next to them" },
  { id: "reference", label: "Reference", hint: "Your solution. It must pass the tests before you can export" },
];

const field = (tab: Tab): "markdown" | "starter" | "tests" | "reference" => (tab === "instructions" ? "markdown" : tab);

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

  const addLesson = (title: string, language: string) =>
    act("add", async () => {
      await saveDraft();
      const { id } = await studio.createLesson(courseId, title, language);
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
                  <span className="hidden shrink-0 group-hover:flex">
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
              <NewLessonForm defaultLanguage={draft?.language ?? course?.language ?? "python"} onAdd={addLesson} onCancel={() => setAdding(false)} />
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
                  <span className="mb-1 block text-xs text-zinc-400">Lesson title</span>
                  <input value={draft.title} onChange={(e) => update({ title: e.target.value })} className={inputClass} />
                </label>
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
                    title="Runs your reference solution and the starter against the tests (⌘ Enter)"
                    className="rounded bg-emerald-700 px-3 py-1.5 font-medium hover:bg-emerald-600 disabled:opacity-40"
                  >
                    Check lesson
                  </button>
                </div>
              </div>

              <div className="flex shrink-0 items-center gap-1 border-b border-zinc-800 px-2 text-xs">
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    className={`border-b-2 px-3 py-2 ${tab === t.id ? "border-indigo-500 text-zinc-100" : "border-transparent text-zinc-400 hover:text-zinc-200"}`}
                  >
                    {t.label}
                    {t.id !== "instructions" && <span className="ml-1 font-mono text-zinc-500">.{ext}</span>}
                  </button>
                ))}
                <span className="ml-auto truncate pr-2 text-zinc-500">{TABS.find((t) => t.id === tab)?.hint}</span>
              </div>

              <div className="flex min-h-0 flex-1">
                <div className={tab === "instructions" ? "w-1/2 border-r border-zinc-800" : "w-full"}>
                  <CodeEditor
                    path={`studio/${courseId}/${draft.id}/${tab}.${tab === "instructions" ? "md" : ext}`}
                    language={tab === "instructions" ? "markdown" : draft.language}
                    value={draft[field(tab)]}
                    onChange={(v) => update({ [field(tab)]: v })}
                    onSave={save}
                    onSubmit={runCheck}
                    autoFocus={false}
                  />
                </div>
                {tab === "instructions" && (
                  <div className="w-1/2 overflow-auto px-6 py-5">
                    <Markdown>{draft.markdown}</Markdown>
                  </div>
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

function NewLessonForm({ defaultLanguage, onAdd, onCancel }: { defaultLanguage: string; onAdd: (title: string, language: string) => void; onCancel: () => void }) {
  const [title, setTitle] = useState("");
  const [language, setLanguage] = useState(defaultLanguage);
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (title.trim()) onAdd(title.trim(), language);
      }}
      className="space-y-2"
    >
      <input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Lesson title" className={inputClass} />
      <select value={language} onChange={(e) => setLanguage(e.target.value)} className={inputClass}>
        {LANGUAGES.map((l) => (
          <option key={l.id} value={l.id}>
            {l.name}
          </option>
        ))}
      </select>
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
