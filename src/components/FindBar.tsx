import { useCallback, useEffect, useLayoutEffect, useRef, useState, type RefObject } from "react";

// The app's webview has no find bar of its own, so ⌘/Ctrl+F opens this one.
// Matches are painted with the CSS Custom Highlight API (styled in index.css)
// rather than by wrapping text in <mark>s, which would fight React over the
// rendered markdown.

const ALL = "fk-find";
const CURRENT = "fk-find-current";

interface Props {
  /** The element whose text is searched. */
  target: RefObject<HTMLElement | null>;
  /** Changes when the target's content does (e.g. the lesson), to search again. */
  contentKey: string;
  /** ⌘/Ctrl+F is ignored while false (e.g. a modal is open). */
  enabled?: boolean;
}

export function FindBar({ target, contentKey, enabled = true }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState<Range[]>([]);
  const [current, setCurrent] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const close = useCallback(() => {
    setOpen(false);
    clearHighlights();
  }, []);

  const step = useCallback(
    (delta: number) => setCurrent((i) => (matches.length ? (i + delta + matches.length) % matches.length : 0)),
    [matches.length],
  );

  // ⌘/Ctrl+F opens (or refocuses) the bar; ⌘/Ctrl+G steps through matches.
  // Monaco handles both itself while the editor has focus.
  useEffect(() => {
    if (!enabled) return;
    const onKey = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey) || e.altKey || e.defaultPrevented) return;
      const key = e.key.toLowerCase();
      if (key === "f" && !e.shiftKey) {
        e.preventDefault();
        setOpen(true);
        // Seed the search with selected lesson text, like a browser does.
        const selected = window.getSelection()?.toString().trim();
        if (selected && !selected.includes("\n") && target.current?.contains(window.getSelection()!.anchorNode)) {
          setQuery(selected);
        }
        requestAnimationFrame(() => inputRef.current?.select());
      } else if (key === "g" && open) {
        e.preventDefault();
        step(e.shiftKey ? -1 : 1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enabled, open, step, target]);

  // Search whenever the query or the content changes; a layout effect, so the
  // matches are in place before the next key (Enter) is handled.
  useLayoutEffect(() => {
    if (!open || !target.current) {
      setMatches([]);
      return;
    }
    setMatches(findRanges(target.current, query));
    setCurrent(0);
  }, [open, query, contentKey, target]);

  // Paint the matches and bring the current one into view.
  useEffect(() => {
    if (!open) return;
    paint(matches, current);
    const range = matches[current];
    const el = range?.startContainer.parentElement;
    if (el && !inView(range, el)) el.scrollIntoView({ block: "center" });
  }, [open, matches, current]);

  useEffect(() => clearHighlights, []);

  if (!open) return null;

  const count = query ? (matches.length ? `${current + 1} of ${matches.length}` : "No matches") : "";

  return (
    <div role="search" className="flex shrink-0 items-center gap-1 border-b border-zinc-800 bg-zinc-950 px-2 py-1 text-xs">
      <input
        ref={inputRef}
        autoFocus
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            step(e.shiftKey ? -1 : 1);
          } else if (e.key === "Escape") {
            e.preventDefault();
            close();
          }
        }}
        placeholder="Find in lesson"
        aria-label="Find in lesson"
        spellCheck={false}
        className="min-w-0 flex-1 rounded border border-zinc-700 bg-zinc-900 px-2 py-1 text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none"
      />
      <span className={`min-w-16 text-right tabular-nums ${query && !matches.length ? "text-red-400" : "text-zinc-500"}`}>{count}</span>
      <FindButton label="Previous match (⇧Enter)" disabled={!matches.length} onClick={() => step(-1)}>
        ↑
      </FindButton>
      <FindButton label="Next match (Enter)" disabled={!matches.length} onClick={() => step(1)}>
        ↓
      </FindButton>
      <FindButton label="Close (Esc)" onClick={close}>
        ✕
      </FindButton>
    </div>
  );
}

function FindButton({ label, disabled, onClick, children }: { label: string; disabled?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      disabled={disabled}
      // Keep focus in the input so Enter keeps stepping.
      onMouseDown={(e) => e.preventDefault()}
      onClick={onClick}
      className="flex h-6 w-6 items-center justify-center rounded text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 disabled:opacity-30 disabled:hover:bg-transparent"
    >
      {children}
    </button>
  );
}

/** Case-insensitive matches of query in root's text, including matches that
 *  span elements (highlighted code splits text into many nodes). */
function findRanges(root: HTMLElement, query: string): Range[] {
  const needle = query.toLowerCase();
  if (!needle) return [];
  const nodes: Text[] = [];
  const starts: number[] = [];
  let text = "";
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    nodes.push(n as Text);
    starts.push(text.length);
    text += n.nodeValue ?? "";
  }
  // Lowercasing can change a string's length (e.g. "İ"); fall back to exact
  // case if so, since offsets must line up with the original text.
  const lower = text.toLowerCase();
  const haystack = lower.length === text.length ? lower : text;
  const ranges: Range[] = [];
  let node = 0;
  const locate = (offset: number, end: boolean) => {
    // Move to the node containing offset (for an end, the one it ends in).
    while (node < nodes.length - 1 && (end ? starts[node + 1] < offset : starts[node + 1] <= offset)) node++;
    return [nodes[node], offset - starts[node]] as const;
  };
  for (let i = haystack.indexOf(needle); i >= 0; i = haystack.indexOf(needle, i + needle.length)) {
    const range = document.createRange();
    range.setStart(...locate(i, false));
    range.setEnd(...locate(i + needle.length, true));
    ranges.push(range);
  }
  return ranges;
}

function inView(range: Range, el: HTMLElement) {
  const r = range.getBoundingClientRect();
  let scroller: HTMLElement | null = el;
  while (scroller && scroller.scrollHeight <= scroller.clientHeight) scroller = scroller.parentElement;
  const box = scroller?.getBoundingClientRect() ?? { top: 0, bottom: window.innerHeight };
  return r.top >= box.top && r.bottom <= box.bottom;
}

function highlights() {
  return typeof CSS !== "undefined" && "highlights" in CSS ? CSS.highlights : undefined;
}

function paint(matches: Range[], current: number) {
  const registry = highlights();
  if (!registry) return;
  registry.set(ALL, new Highlight(...matches.filter((_, i) => i !== current)));
  registry.set(CURRENT, new Highlight(...(matches[current] ? [matches[current]] : [])));
}

function clearHighlights() {
  highlights()?.delete(ALL);
  highlights()?.delete(CURRENT);
}
