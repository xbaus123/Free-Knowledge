import { useMemo, useState } from "react";

export interface TreeFile {
  path: string;
  readOnly?: boolean;
}

interface Props {
  files: TreeFile[];
  active?: string;
  onOpen: (path: string) => void;
  /** Optional per-file actions (e.g. delete or lock in the Studio). */
  renderActions?: (file: TreeFile) => React.ReactNode;
}

type Folder = { name: string; path: string; folders: Folder[]; files: TreeFile[] };

function buildTree(files: TreeFile[]): Folder {
  const root: Folder = { name: "", path: "", folders: [], files: [] };
  for (const f of files) {
    const parts = f.path.split("/");
    let dir = root;
    for (const part of parts.slice(0, -1)) {
      const path = dir.path ? `${dir.path}/${part}` : part;
      let next = dir.folders.find((d) => d.name === part);
      if (!next) {
        next = { name: part, path, folders: [], files: [] };
        dir.folders.push(next);
      }
      dir = next;
    }
    dir.files.push(f);
  }
  const sort = (d: Folder) => {
    d.folders.sort((a, b) => a.name.localeCompare(b.name));
    d.files.sort((a, b) => a.path.localeCompare(b.path));
    d.folders.forEach(sort);
  };
  sort(root);
  return root;
}

/** A collapsible folder tree of a lesson's files. */
export function FileTree({ files, active, onOpen, renderActions }: Props) {
  const tree = useMemo(() => buildTree(files), [files]);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  const toggle = (path: string) =>
    setCollapsed((c) => {
      const next = new Set(c);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });

  const renderFolder = (folder: Folder, depth: number): React.ReactNode => (
    <>
      {folder.folders.map((d) => (
        <li key={d.path}>
          <button
            onClick={() => toggle(d.path)}
            style={{ paddingLeft: 8 + depth * 12 }}
            className="flex w-full items-center gap-1.5 py-1 pr-2 text-left text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
          >
            <span className="w-3 text-[10px]">{collapsed.has(d.path) ? "▸" : "▾"}</span>
            <span className="truncate">{d.name}</span>
          </button>
          {!collapsed.has(d.path) && <ul>{renderFolder(d, depth + 1)}</ul>}
        </li>
      ))}
      {folder.files.map((f) => (
        <li key={f.path} className="group flex items-center">
          <button
            onClick={() => onOpen(f.path)}
            title={f.readOnly ? `${f.path} (read-only)` : f.path}
            style={{ paddingLeft: 20 + depth * 12 }}
            className={`flex min-w-0 flex-1 items-center gap-1.5 py-1 pr-2 text-left ${
              f.path === active ? "bg-zinc-800 text-zinc-100" : "text-zinc-300 hover:bg-zinc-900"
            }`}
          >
            <span className="truncate">{f.path.split("/").pop()}</span>
            {f.readOnly && <LockIcon />}
          </button>
          {renderActions && <span className="flex shrink-0 pr-1">{renderActions(f)}</span>}
        </li>
      ))}
    </>
  );

  return <ul className="py-1 text-[13px]">{renderFolder(tree, 0)}</ul>;
}

export function LockIcon({ className = "h-3 w-3 shrink-0 text-amber-400/80" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-label="read-only">
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </svg>
  );
}
