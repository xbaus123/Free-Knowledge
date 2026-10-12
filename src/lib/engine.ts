// Client for the Go engine sidecar. Connection details (including the
// per-launch auth token) come from the Rust side via `engine_info`.
import { invoke } from "@tauri-apps/api/core";

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

interface EngineInfo {
  baseUrl: string;
  wsUrl: string;
  token: string;
}

let infoPromise: Promise<EngineInfo> | undefined;
function engineInfo(): Promise<EngineInfo> {
  infoPromise ??= invoke<EngineInfo>("engine_info").catch((err) => {
    infoPromise = undefined;
    throw err;
  });
  return infoPromise;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { baseUrl, token } = await engineInfo();
  const res = await fetch(baseUrl + path, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.error ?? `engine returned ${res.status}`);
  return body as T;
}

export const health = () => request<Health>("/health");
export const runtimes = () => request<RuntimeInfo[]>("/runtimes");
export const run = (req: RunRequest) => request<RunResult>("/run", { method: "POST", body: JSON.stringify(req) });

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

/** Runs code over WebSocket, streaming output as it arrives. */
export function runStreaming(req: RunRequest, handlers: StreamHandlers): { result: Promise<RunResult>; cancel: () => void } {
  let ws: WebSocket | undefined;
  let cancelled = false;

  const result = engineInfo().then(
    ({ wsUrl, token }) =>
      new Promise<RunResult>((resolve, reject) => {
        if (cancelled) return reject(new Error("cancelled"));
        ws = new WebSocket(`${wsUrl}/ws/run?token=${encodeURIComponent(token)}`);
        let settled = false;
        ws.onopen = () => ws!.send(JSON.stringify({ type: "run", ...req }));
        ws.onmessage = (ev) => {
          const msg = JSON.parse(ev.data);
          if (msg.type === "output") handlers.onOutput(msg.stream, msg.data, msg.phase);
          else if (msg.type === "result") {
            settled = true;
            const { type: _, ...res } = msg;
            resolve(res as RunResult);
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
