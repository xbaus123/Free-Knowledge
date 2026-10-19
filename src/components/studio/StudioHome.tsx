import { useCallback, useEffect, useState } from "react";
import * as engine from "../../lib/engine";
import * as studio from "../../lib/studio";

interface Props {
  onHome: () => void;
  onEdit: (courseId: string) => void;
}

export function StudioHome({ onHome, onEdit }: Props) {
  const [courses, setCourses] = useState<engine.Course[]>();
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState<string>();

  const refresh = useCallback(() => {
    engine.courses().then(setCourses, (e) => setError(String(e)));
  }, []);
  useEffect(refresh, [refresh]);

  const run = async (label: string, fn: () => Promise<void>) => {
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

  const doImport = () =>
    run("import", async () => {
      const res = await studio.importWithPrompts();
      if (!res) return;
      setNotice(`${res.replaced ? "Replaced" : "Imported"} "${res.title}" (${res.lessons} lesson${res.lessons === 1 ? "" : "s"}).`);
      refresh();
    });

  const yours = courses?.filter((c) => c.source === "user") ?? [];
  const bundled = courses?.filter((c) => c.source === "bundled") ?? [];

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-5xl px-6 py-8">
        <button onClick={onHome} className="mb-4 rounded px-2 py-1 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
          ← Home
        </button>
        <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Creator Studio</h1>
            <p className="text-sm text-zinc-400">Write lessons, check them against your reference solution, and share them as .dojo files.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={doImport} disabled={!!busy} className="rounded border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-800 disabled:opacity-40">
              Import .dojo
            </button>
            <button onClick={() => setCreating(true)} className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium hover:bg-indigo-500">
              New course
            </button>
          </div>
        </header>

        {error && <p className="mb-4 rounded border border-red-900 bg-red-950/40 p-3 text-sm text-red-300">{error}</p>}
        {notice && <p className="mb-4 rounded border border-emerald-900 bg-emerald-950/40 p-3 text-sm text-emerald-300">{notice}</p>}

        {creating && (
          <NewCourseForm
            onCancel={() => setCreating(false)}
            onCreate={(meta) =>
              run("create", async () => {
                const { id } = await studio.createCourse(meta);
                onEdit(id);
              })
            }
          />
        )}

        <h2 className="mb-3 text-sm font-medium tracking-wide text-zinc-400 uppercase">Your courses</h2>
        {courses && yours.length === 0 && (
          <p className="mb-8 text-sm text-zinc-500">Nothing yet. Create a course, import a .dojo, or copy a bundled course below to see how one is built.</p>
        )}
        <div className="mb-10 grid gap-3 sm:grid-cols-2">
          {yours.map((c) => (
            <div key={c.id} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <h3 className="font-medium">{c.title}</h3>
              <p className="mb-3 line-clamp-2 text-sm text-zinc-400">{c.description || <span className="text-zinc-600">No description</span>}</p>
              <div className="flex items-center gap-2 text-sm">
                <span className="mr-auto text-xs text-zinc-500">
                  {c.lessons.length} lesson{c.lessons.length === 1 ? "" : "s"}
                  {c.problems?.length ? ` · ⚠ ${c.problems.length} problem${c.problems.length > 1 ? "s" : ""}` : ""}
                </span>
                <button
                  onClick={() =>
                    run("delete", async () => {
                      if (!(await studio.confirmDialog(`Delete "${c.title}" and all its lessons? This can't be undone.`))) return;
                      await studio.deleteCourse(c.id);
                      refresh();
                    })
                  }
                  disabled={!!busy}
                  className="rounded px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-800 hover:text-red-400"
                >
                  Delete
                </button>
                <button onClick={() => onEdit(c.id)} className="rounded bg-zinc-700 px-3 py-1 hover:bg-zinc-600">
                  Edit
                </button>
              </div>
            </div>
          ))}
        </div>

        {bundled.length > 0 && (
          <>
            <h2 className="mb-1 text-sm font-medium tracking-wide text-zinc-400 uppercase">Bundled courses</h2>
            <p className="mb-3 text-xs text-zinc-500">These ship with the app and can't be edited directly. Make a copy to remix one.</p>
            <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800">
              {bundled.map((c) => (
                <li key={c.id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                  <span>
                    {c.title} <span className="text-xs text-zinc-500">· {c.lessons.length} lessons</span>
                  </span>
                  <button
                    onClick={() =>
                      run("copy", async () => {
                        const { id } = await studio.copyCourse(c.id);
                        onEdit(id);
                      })
                    }
                    disabled={!!busy}
                    className="rounded border border-zinc-700 px-2.5 py-1 text-xs hover:bg-zinc-800 disabled:opacity-40"
                  >
                    Make an editable copy
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}

function NewCourseForm({ onCreate, onCancel }: { onCreate: (meta: Partial<studio.CourseMeta>) => void; onCancel: () => void }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [author, setAuthor] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (title.trim()) onCreate({ title: title.trim(), description, author });
      }}
      className="mb-8 grid gap-3 rounded-lg border border-indigo-900 bg-zinc-900/60 p-4 sm:grid-cols-2"
    >
      <Field label="Title">
        <input autoFocus value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Intro to Recursion" className={inputClass} />
      </Field>
      <Field label="Author">
        <input value={author} onChange={(e) => setAuthor(e.target.value)} placeholder="Your name" className={inputClass} />
      </Field>
      <Field label="Description" wide>
        <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What will learners be able to do?" className={inputClass} />
      </Field>
      <p className="self-end text-xs text-zinc-500">Each lesson picks its own languages, and can mix several.</p>
      <div className="flex items-end justify-end gap-2">
        <button type="button" onClick={onCancel} className="rounded px-3 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800">
          Cancel
        </button>
        <button type="submit" disabled={!title.trim()} className="rounded bg-indigo-600 px-3 py-1.5 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40">
          Create course
        </button>
      </div>
    </form>
  );
}

export const inputClass = "w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm outline-none focus:border-indigo-500";

export function Field({ label, wide, children }: { label: string; wide?: boolean; children: React.ReactNode }) {
  return (
    <label className={`block ${wide ? "sm:col-span-2" : ""}`}>
      <span className="mb-1 block text-xs text-zinc-400">{label}</span>
      {children}
    </label>
  );
}
