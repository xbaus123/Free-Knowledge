import type { SimEvent, Timeline } from "../../lib/engine";

interface Props {
  timeline: Timeline;
  frame: number;
  onFrame: (frame: number) => void;
  playing: boolean;
  onTogglePlay: () => void;
}

const EVENT_COLORS: Record<SimEvent["kind"], string> = {
  crash: "bg-red-500",
  partition: "bg-red-500",
  failover: "bg-emerald-500",
  bottleneck: "bg-amber-400",
  queueing: "bg-amber-600",
  errors: "bg-red-400",
  data_loss: "bg-fuchsia-500",
  stale: "bg-yellow-400",
  throttled: "bg-orange-400",
  deploy: "bg-sky-400",
  lock: "bg-blue-400",
};

/** Replay controls: play/pause, step, and a slider with event markers. */
export function TimelineScrubber({ timeline, frame, onFrame, playing, onTogglePlay }: Props) {
  const last = timeline.frames.length - 1;
  if (last < 0) return null;
  const current = timeline.frames[frame];
  const end = timeline.frames.length * timeline.intervalMs;

  return (
    <div
      className="shrink-0 border-t border-zinc-800 bg-zinc-950 px-3 py-2 text-xs"
      onKeyDown={(e) => {
        if (e.key === "ArrowRight") onFrame(Math.min(last, frame + 1));
        else if (e.key === "ArrowLeft") onFrame(Math.max(0, frame - 1));
        else return;
        e.preventDefault();
      }}
    >
      <div className="flex items-center gap-2">
        <button
          onClick={onTogglePlay}
          aria-label={playing ? "Pause replay" : "Play replay"}
          className="w-14 rounded bg-zinc-800 px-2 py-1 font-medium text-zinc-200 hover:bg-zinc-700"
        >
          {playing ? "❚❚ Pause" : frame >= last ? "↺ Replay" : "▶ Play"}
        </button>
        <button onClick={() => onFrame(Math.max(0, frame - 1))} disabled={frame === 0} aria-label="Previous frame" className="rounded px-1.5 py-1 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30">
          ‹
        </button>
        <button onClick={() => onFrame(Math.min(last, frame + 1))} disabled={frame === last} aria-label="Next frame" className="rounded px-1.5 py-1 text-zinc-400 hover:bg-zinc-800 disabled:opacity-30">
          ›
        </button>

        <div className="relative flex-1">
          {/* Event markers sit above the track; click one to jump there. */}
          <div className="pointer-events-none absolute -top-1.5 right-0 left-0 h-1.5">
            {timeline.events.map((e, i) => (
              <button
                key={i}
                title={`${Math.round(e.t)} ms: ${e.message}`}
                aria-label={`${Math.round(e.t)} ms: ${e.message}`}
                onClick={() => onFrame(Math.min(last, Math.floor(e.t / timeline.intervalMs)))}
                style={{ left: `${(e.t / end) * 100}%` }}
                className={`pointer-events-auto absolute h-1.5 w-1.5 -translate-x-1/2 rounded-full ${EVENT_COLORS[e.kind] ?? "bg-zinc-400"}`}
              />
            ))}
          </div>
          <input
            type="range"
            min={0}
            max={last}
            value={frame}
            onChange={(e) => onFrame(Number(e.target.value))}
            aria-label="Replay position"
            className="w-full accent-indigo-500"
          />
        </div>

        <span className="w-32 shrink-0 text-right font-mono text-zinc-300">
          {Math.round(current.t)}–{Math.round(current.t + timeline.intervalMs)} ms
        </span>
        <span className="w-36 shrink-0 text-right text-zinc-500">
          <span className="text-emerald-400">{current.completed}</span> done
          {current.failed > 0 && (
            <>
              , <span className="text-red-400">{current.failed}</span> failed
            </>
          )}
        </span>
      </div>
    </div>
  );
}
