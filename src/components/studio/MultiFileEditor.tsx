import { useState } from "react";
import { languageForPath } from "../../lib/monaco";
import { CodeEditor } from "../CodeEditor";
import { FileTree, LockIcon } from "../FileTree";
import { inputClass } from "./StudioHome";

interface Props {
  /** "starter": the files learners start with. "reference": your solution versions of the editable ones. */
  mode: "starter" | "reference";
  idPrefix: string;
  starterFiles: Record<string, string>;
  referenceFiles: Record<string, string>;
  readOnly: string[];
  /** Extension for new files, e.g. "py". */
  ext: string;
  onChange: (next: { starterFiles: Record<string, string>; referenceFiles: Record<string, string>; readOnly: string[] }) => void;
  onSave: () => void;
  onSubmit: () => void;
}

// Mirrors the engine's rules (course.ValidFilePath / ReservedFilePath).
const SEGMENT = /^[A-Za-z0-9_][A-Za-z0-9._-]{0,63}$/;
function fileNameProblem(path: string, existing: Record<string, string>): string | undefined {
  const parts = path.split("/");
  if (!path) return "Enter a file name";
  if (parts.length > 4 || path.length > 200 || parts.some((p) => !SEGMENT.test(p) || p.includes(".."))) {
    return "Use letters, digits, . _ - and / for folders (up to 4 deep)";
  }
  const base = parts[parts.length - 1];
  if (path === "go.mod" || path === "package.json" || base.startsWith("solution_test.") || base.startsWith("fk_")) return "That name is reserved for the grader";
  if (path in existing) return "That file already exists";
}

/** File tree plus editor for a multi-file lesson's starter or reference files. */
export function MultiFileEditor({ mode, idPrefix, starterFiles, referenceFiles, readOnly, ext, onChange, onSave, onSubmit }: Props) {
  const paths = Object.keys(starterFiles).sort();
  const visible = mode === "starter" ? paths : paths.filter((p) => !readOnly.includes(p));
  const [selected, setSelected] = useState(() => visible.find((p) => p.startsWith("solution.")) ?? visible[0] ?? "");
  const [adding, setAdding] = useState(false);
  const [newName, setNewName] = useState("");
  const active = visible.includes(selected) ? selected : (visible[0] ?? "");
  const problem = adding ? fileNameProblem(newName.trim(), starterFiles) : undefined;

  const emit = (patch: Partial<{ starterFiles: Record<string, string>; referenceFiles: Record<string, string>; readOnly: string[] }>) =>
    onChange({ starterFiles, referenceFiles, readOnly, ...patch });

  const addFile = () => {
    const path = newName.trim();
    if (fileNameProblem(path, starterFiles)) return;
    emit({ starterFiles: { ...starterFiles, [path]: "" } });
    setSelected(path);
    setAdding(false);
    setNewName("");
  };

  const removeFile = (path: string) => {
    const { [path]: _s, ...starter } = starterFiles;
    const { [path]: _r, ...reference } = referenceFiles;
    emit({ starterFiles: starter, referenceFiles: reference, readOnly: readOnly.filter((p) => p !== path) });
  };

  const toggleLock = (path: string) =>
    emit({ readOnly: readOnly.includes(path) ? readOnly.filter((p) => p !== path) : [...readOnly, path] });

  // Reference files default to the starter version until you change them.
  const content = mode === "starter" ? (starterFiles[active] ?? "") : (referenceFiles[active] ?? starterFiles[active] ?? "");
  const setContent = (value: string) =>
    mode === "starter" ? emit({ starterFiles: { ...starterFiles, [active]: value } }) : emit({ referenceFiles: { ...referenceFiles, [active]: value } });

  return (
    <div className="flex h-full w-full">
      <nav className="flex w-56 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950" aria-label="Lesson files">
        <div className="min-h-0 flex-1 overflow-auto">
          <FileTree
            files={visible.map((p) => ({ path: p, readOnly: readOnly.includes(p) }))}
            active={active}
            onOpen={setSelected}
            renderActions={
              mode === "starter"
                ? (f) => (
                    <span className="flex gap-0.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100">
                      <button
                        onClick={() => toggleLock(f.path)}
                        title={f.readOnly ? "Unlock: learners can edit it" : "Lock: learners can read it but not edit it"}
                        aria-label={f.readOnly ? `Unlock ${f.path}` : `Lock ${f.path}`}
                        className="rounded px-1 py-0.5 text-zinc-500 hover:bg-zinc-800 hover:text-amber-300"
                      >
                        <LockIcon className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => removeFile(f.path)}
                        disabled={paths.length === 1}
                        title="Delete file"
                        aria-label={`Delete ${f.path}`}
                        className="rounded px-1 py-0.5 text-xs text-zinc-500 hover:bg-zinc-800 hover:text-red-400 disabled:hidden"
                      >
                        ✕
                      </button>
                    </span>
                  )
                : undefined
            }
          />
        </div>
        {mode === "starter" ? (
          <div className="border-t border-zinc-800 p-2 text-xs">
            {adding ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  addFile();
                }}
                className="space-y-1.5"
              >
                <input
                  autoFocus
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder={`helpers.${ext}, app.js, index.html…`}
                  className={inputClass}
                  aria-label="New file name"
                />
                {newName && problem && <p className="text-[11px] text-amber-400">{problem}</p>}
                <div className="flex justify-end gap-1">
                  <button type="button" onClick={() => setAdding(false)} className="rounded px-2 py-1 text-zinc-400 hover:bg-zinc-800">
                    Cancel
                  </button>
                  <button type="submit" disabled={!!problem} className="rounded bg-indigo-600 px-2 py-1 font-medium hover:bg-indigo-500 disabled:opacity-40">
                    Add
                  </button>
                </div>
              </form>
            ) : (
              <>
                <button onClick={() => setAdding(true)} className="w-full rounded px-2 py-1.5 text-left text-indigo-300 hover:bg-zinc-900">
                  + Add file
                </button>
                <p className="px-2 pt-1 text-[11px] text-zinc-500">Hover a file to lock it (learners can read but not edit) or delete it.</p>
              </>
            )}
          </div>
        ) : (
          <p className="border-t border-zinc-800 p-3 text-[11px] text-zinc-500">
            Locked files aren't listed: grading always uses the starter version of them.
          </p>
        )}
      </nav>
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex h-8 shrink-0 items-center gap-2 border-b border-zinc-800 px-3 font-mono text-xs text-zinc-400">
          {active || "No files"}
          {readOnly.includes(active) && (
            <span className="flex items-center gap-1 font-sans text-[11px] text-amber-400/80">
              <LockIcon /> learners can't edit this file
            </span>
          )}
        </div>
        <div className="min-h-0 flex-1">
          {active && (
            <CodeEditor
              path={`studio/${idPrefix}/${mode}/${active}`}
              language={languageForPath(active)}
              value={content}
              onChange={setContent}
              onSave={onSave}
              onSubmit={onSubmit}
              autoFocus={false}
            />
          )}
        </div>
      </div>
    </div>
  );
}
