/** A ribbon bookmark; filled when the bookmark is set. */
export function BookmarkIcon({ filled, className = "h-3.5 w-3.5" }: { filled?: boolean; className?: string }) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" className={className} fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.5">
      <path d="M4 2.75h8v10.5l-4-2.75-4 2.75z" strokeLinejoin="round" />
    </svg>
  );
}
