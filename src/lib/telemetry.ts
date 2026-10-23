// Local learning telemetry for lessons that enable it. Records counts and
// durations only (never code or what was typed), and stores them on this
// device through the engine. Learners can switch it off.
import * as engine from "./engine";

const OFF_KEY = "fk:telemetry-off";
/** A keystroke counts the next few seconds as active typing. */
const TYPING_WINDOW_MS = 4_000;
/** With no input for this long, time stops counting as reading. */
const IDLE_AFTER_MS = 90_000;
const TICK_MS = 1_000;
const FLUSH_EVERY_MS = 30_000;

export function telemetryAllowed(): boolean {
  try {
    return localStorage.getItem(OFF_KEY) !== "1";
  } catch {
    return true;
  }
}

export function setTelemetryAllowed(allowed: boolean) {
  try {
    if (allowed) localStorage.removeItem(OFF_KEY);
    else localStorage.setItem(OFF_KEY, "1");
  } catch {
    // Storage unavailable: the choice lasts for this session only.
  }
}

/** Sorts a graded submission into an error category. */
export function classifyGrade(r: engine.GradeResult): engine.Outcome {
  if (r.passed) return "pass";
  if (r.timedOut) return "timeout";
  if (r.phase === "compile") return "compile_error";
  if (r.tests.length === 0) return /\b(SyntaxError|IndentationError|TabError)\b/.test(r.stderr) ? "syntax_error" : "runtime_error";
  if (r.tests.some((t) => t.status === "error")) return "runtime_error";
  return "failed_assertion";
}

/** Tracks one visit to a lesson. Call dispose() when leaving it. */
export class LessonTelemetry {
  private session: engine.TelemetrySession;
  private lastKey = 0;
  private lastActivity = Date.now();
  private lastTick = Date.now();
  private dirty = false;
  private stopped = false;
  private timers: number[] = [];
  private readonly courseId: string;
  private readonly lessonId: string;

  constructor(courseId: string, lessonId: string) {
    this.courseId = courseId;
    this.lessonId = lessonId;
    this.session = {
      sessionId: crypto.randomUUID(),
      startedAt: new Date().toISOString(),
      readingMs: 0,
      typingMs: 0,
      keystrokes: 0,
      submissions: 0,
      runs: 0,
      outcomes: {},
      solved: false,
    };
    for (const type of ["pointermove", "pointerdown", "wheel", "keydown"]) window.addEventListener(type, this.onActivity, { passive: true });
    document.addEventListener("visibilitychange", this.onVisibility);
    this.timers.push(window.setInterval(this.tick, TICK_MS), window.setInterval(() => this.flush(), FLUSH_EVERY_MS));
  }

  /** An edit in the lesson's editor or canvas. */
  keystroke() {
    this.session.keystrokes++;
    this.lastKey = this.lastActivity = Date.now();
    this.dirty = true;
  }

  /** A run that isn't graded: the scratchpad, Run, or a chaos experiment. */
  run() {
    this.session.runs++;
    this.dirty = true;
  }

  submission(outcome: engine.Outcome) {
    this.session.submissions++;
    this.session.outcomes[outcome] = (this.session.outcomes[outcome] ?? 0) + 1;
    if (outcome === "pass") this.session.solved = true;
    this.dirty = true;
    this.flush();
  }

  /** Saves the session's totals so far; returns once saved. */
  async flush() {
    if (!this.dirty) return;
    this.dirty = false;
    try {
      await engine.saveTelemetry(this.courseId, this.lessonId, { ...this.session, outcomes: { ...this.session.outcomes } });
    } catch {
      this.dirty = true; // retry on the next flush
    }
  }

  /** Stops tracking and saves what's left. */
  dispose() {
    if (this.stopped) return;
    this.stop();
    this.tick();
    void this.flush();
  }

  /** Stops tracking without saving (after the learner clears their data). */
  discard() {
    this.stop();
    this.dirty = false;
  }

  private stop() {
    this.stopped = true;
    this.timers.forEach((t) => window.clearInterval(t));
    for (const type of ["pointermove", "pointerdown", "wheel", "keydown"]) window.removeEventListener(type, this.onActivity);
    document.removeEventListener("visibilitychange", this.onVisibility);
  }

  private onActivity = () => {
    this.lastActivity = Date.now();
  };

  private onVisibility = () => {
    if (document.visibilityState === "hidden") void this.flush();
  };

  private tick = () => {
    const now = Date.now();
    const elapsed = Math.min(now - this.lastTick, 5 * TICK_MS); // ignore gaps from sleep
    this.lastTick = now;
    if (document.visibilityState !== "visible" || !document.hasFocus()) return;
    if (now - this.lastKey < TYPING_WINDOW_MS) this.session.typingMs += elapsed;
    else if (now - this.lastActivity < IDLE_AFTER_MS) this.session.readingMs += elapsed;
    else return;
    this.dirty = true;
  };
}
