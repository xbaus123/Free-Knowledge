// Client for the Go engine sidecar. Connection details (including the
// per-launch auth token) come from the Rust side via `engine_info`.
import { invoke, isTauri } from "@tauri-apps/api/core";

export type Phase = "compile" | "run";

export interface RunRequest {
  language: string;
  code: string;
  stdin?: string;
  timeoutMs?: number;
}

export interface RunResult {
  phase: Phase;
  exitCode: number;
  stdout: string;
  stderr: string;
  timedOut: boolean;
  truncated: boolean;
  durationMs: number;
  error?: string;
}

export interface RuntimeInfo {
  id: string;
  name: string;
  file: string;
  requires: string;
  available: boolean;
  path?: string;
}

export interface Health {
  status: string;
  version: string;
}

export interface LessonSummary {
  id: string;
  title: string;
  language: string;
  kind: string;
  problems?: string[];
}

export interface Course {
  id: string;
  title: string;
  description: string;
  author?: string;
  version?: string;
  language?: string;
  source: "user" | "bundled";
  lessons: LessonSummary[];
  problems?: string[];
}

export interface Lesson extends LessonSummary {
  courseId: string;
  markdown: string;
  /** Starter code, or diagram JSON for system design lessons. */
  starter: string;
  timeoutMs: number;
  /** System design: p99 latency target. */
  maxLatencyMs?: number;
  /** Quiz: answer choices. */
  options?: string[];
}

export const isDesignLesson = (l?: LessonSummary) => l?.kind === "system-design";
export const isArticleLesson = (l?: LessonSummary) => l?.kind === "article";
export const isQuizLesson = (l?: LessonSummary) => l?.kind === "quiz";

export interface SimNodeStats {
  type: string;
  label: string;
  processed: number;
  /** 0..1 */
  utilization: number;
  maxQueue: number;
}

export interface SimResult {
  passed: boolean;
  message: string;
  issues: { nodeId?: string; code: string; message: string }[];
  metrics: {
    requests: number;
    completed: number;
    failed: number;
    p50Ms: number;
    p95Ms: number;
    p99Ms: number;
    maxMs: number;
    durationMs: number;
    throughputPerSec: number;
    maxLatencyMs?: number;
  };
  nodes: Record<string, SimNodeStats>;
}

export type TestStatus = "pass" | "fail" | "error" | "skip";

export interface TestResult {
  name: string;
  status: TestStatus;
  message?: string;
  durationMs: number;
}

export interface GradeResult extends RunResult {
  passed: boolean;
  tests: TestResult[];
}

export interface LessonProgress {
  completed: boolean;
  completedAt?: string;
  attempts: number;
  hasCode: boolean;
}

export interface LessonProgressDetail extends LessonProgress {
  code: string | null;
  codeUpdatedAt?: string;
}

export interface Progress {
  stats: { currentStreak: number; completedLessons: number };
  /** courseId → lessonId → progress; lessons with no activity are absent. */
  courses: Record<string, Record<string, LessonProgress>>;
}

interface EngineInfo {
  baseUrl: string;
  wsUrl: string;
  token: string;
}

let infoPromise: Promise<EngineInfo> | undefined;
function engineInfo(): Promise<EngineInfo> {
  // `npm run dev:web` runs the UI in a plain browser against `npm run dev:engine`,
  // on separate ports so it can run alongside `npm run tauri dev`.
  const devToken = import.meta.env.DEV && !isTauri() ? import.meta.env.VITE_FK_ENGINE_TOKEN : undefined;
  if (devToken) {
    const addr = `127.0.0.1:${import.meta.env.VITE_FK_ENGINE_PORT ?? "14210"}`;
    return Promise.resolve({ baseUrl: `http://${addr}`, wsUrl: `ws://${addr}`, token: devToken });
  }

  infoPromise ??= invoke<EngineInfo>("engine_info").catch((err) => {
    infoPromise = undefined;
    throw err;
  });
  return infoPromise;
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { baseUrl, token } = await engineInfo();
  const res = await fetch(baseUrl + path, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  });
  if (res.status === 204) return undefined as T;
  const body = await res.json();
  if (!res.ok) throw new EngineError(body.error ?? `engine returned ${res.status}`, res.status, body);
  return body as T;
}

/** An error response from the engine; `body` has any extra fields it sent. */
export class EngineError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body: Record<string, unknown>,
  ) {
    super(message);
  }
}

export const health = () => request<Health>("/health");
export const runtimes = () => request<RuntimeInfo[]>("/runtimes");
export const run = (req: RunRequest) => request<RunResult>("/run", { method: "POST", body: JSON.stringify(req) });

const lessonPath = (courseId: string, lessonId: string) =>
  `/courses/${encodeURIComponent(courseId)}/lessons/${encodeURIComponent(lessonId)}`;

export const courses = () => request<Course[]>("/courses");
export const course = (id: string) => request<Course>(`/courses/${encodeURIComponent(id)}`);
export const lesson = (courseId: string, lessonId: string) => request<Lesson>(lessonPath(courseId, lessonId));
export const submit = (courseId: string, lessonId: string, code: string) =>
  request<GradeResult>(lessonPath(courseId, lessonId) + "/submit", { method: "POST", body: JSON.stringify({ code }) });

export const progress = () => request<Progress>("/progress");
export const lessonProgress = (courseId: string, lessonId: string) =>
  request<LessonProgressDetail>(lessonPath(courseId, lessonId) + "/progress");
export const saveCode = (courseId: string, lessonId: string, code: string) =>
  request<void>(lessonPath(courseId, lessonId) + "/progress/code", { method: "PUT", body: JSON.stringify({ code }) });
export const resetCode = (courseId: string, lessonId: string) =>
  request<void>(lessonPath(courseId, lessonId) + "/progress/code", { method: "DELETE" });

/** Grades a quiz answer (zero-based index into the lesson's options). */
export const submitAnswer = (courseId: string, lessonId: string, answer: number) =>
  request<GradeResult>(lessonPath(courseId, lessonId) + "/submit", { method: "POST", body: JSON.stringify({ answer }) });

/** Marks an article lesson as read. */
export const completeArticle = (courseId: string, lessonId: string) =>
  request<GradeResult>(lessonPath(courseId, lessonId) + "/submit", { method: "POST", body: "{}" });

/** Sends a burst of traffic through a system design diagram and grades it. */
export const simulate = (courseId: string, lessonId: string, graphJson: string) =>
  request<SimResult>("/simulate", {
    method: "POST",
    body: `{"course":${JSON.stringify(courseId)},"lesson":${JSON.stringify(lessonId)},"graph":${graphJson}}`,
  });

/** Polls /health until the engine answers, since it starts alongside the window. */
export async function waitForEngine(timeoutMs = 10_000): Promise<Health> {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    try {
      return await health();
    } catch (err) {
      if (Date.now() > deadline) throw err;
      await new Promise((r) => setTimeout(r, 250));
    }
  }
}

export interface StreamHandlers {
  onOutput: (stream: "stdout" | "stderr", data: string, phase: Phase) => void;
}

export interface Streamed<T> {
  result: Promise<T>;
  cancel: () => void;
}

/** Runs code over WebSocket, streaming output as it arrives. */
export const runStreaming = (req: RunRequest, handlers: StreamHandlers) =>
  stream<RunResult>({ type: "run", ...req }, "result", handlers);

/** Grades code against a lesson's hidden tests, streaming program output. */
export const submitStreaming = (courseId: string, lessonId: string, code: string, handlers: StreamHandlers) =>
  stream<GradeResult>({ type: "submit", course: courseId, lesson: lessonId, code }, "grade", handlers);

function stream<T>(message: object, resultType: string, handlers: StreamHandlers): Streamed<T> {
  let ws: WebSocket | undefined;
  let cancelled = false;

  const result = engineInfo().then(
    ({ wsUrl, token }) =>
      new Promise<T>((resolve, reject) => {
        if (cancelled) return reject(new Error("cancelled"));
        ws = new WebSocket(`${wsUrl}/ws/run?token=${encodeURIComponent(token)}`);
        let settled = false;
        ws.onopen = () => ws!.send(JSON.stringify(message));
        ws.onmessage = (ev) => {
          const msg = JSON.parse(ev.data);
          if (msg.type === "output") handlers.onOutput(msg.stream, msg.data, msg.phase);
          else if (msg.type === resultType) {
            settled = true;
            const { type: _, ...res } = msg;
            resolve(res as T);
          } else if (msg.type === "error") {
            settled = true;
            reject(new Error(msg.error));
          }
        };
        ws.onerror = () => {
          if (!settled) reject(new Error("engine connection failed"));
        };
        ws.onclose = () => {
          if (!settled) reject(new Error(cancelled ? "cancelled" : "engine closed the connection"));
        };
      }),
  );

  return {
    result,
    cancel: () => {
      cancelled = true;
      if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "cancel" }));
      ws?.close();
    },
  };
}
