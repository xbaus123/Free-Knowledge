// Creator Studio API, plus native dialogs with browser fallbacks for
// `npm run dev:web`.
import { isTauri } from "@tauri-apps/api/core";
import { ask, message, open, save } from "@tauri-apps/plugin-dialog";
import { EngineError, request, type Capabilities, type GradeResult, type SimResult } from "./engine";

export interface CourseMeta {
  title: string;
  description: string;
  author: string;
  version: string;
  language?: string;
}

export type LessonType = "code" | "article" | "quiz" | "system-design";

export interface LessonSource {
  id: string;
  /** Chosen when the lesson is created; can't change. */
  type: LessonType;
  title: string;
  language?: string;
  timeoutMs?: number;
  /** System design: p99 latency target. */
  maxLatencyMs?: number;
  markdown: string;
  /** Code: starter code. System design: starter diagram JSON. */
  starter: string;
  tests: string;
  /** Code: reference solution. System design: solution diagram JSON. */
  reference: string;
  questions?: QuestionSource[];
  capabilities: Capabilities;
  /** Multi-file code lessons: starting files, path → content. */
  starterFiles?: Record<string, string>;
  /** Multi-file code lessons: your solution versions of the editable files. */
  referenceFiles?: Record<string, string>;
}

/** A quiz question including its answer, as authors see it. */
export interface QuestionSource {
  prompt: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export interface LessonCheck {
  lessonId: string;
  title: string;
  ok: boolean;
  problem?: string;
  warning?: string;
}

export interface LessonCheckDetail extends LessonCheck {
  reference?: GradeResult;
  starter?: GradeResult;
  /** System design lessons: simulator runs of solution.json and starter.json. */
  referenceSim?: SimResult;
  starterSim?: SimResult;
}

export interface ImportResult {
  id: string;
  title: string;
  lessons: number;
  replaced: boolean;
  problems?: string[];
}

const enc = encodeURIComponent;
const coursePath = (id: string) => `/studio/courses/${enc(id)}`;
const lessonPath = (courseId: string, lessonId: string) => `${coursePath(courseId)}/lessons/${enc(lessonId)}`;
const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });

export const createCourse = (meta: Partial<CourseMeta>) => request<{ id: string }>("/studio/courses", json("POST", meta));
export const updateCourse = (id: string, meta: CourseMeta, lessons?: string[]) =>
  request<void>(coursePath(id), json("PUT", { ...meta, lessons }));
export const deleteCourse = (id: string) => request<void>(coursePath(id), { method: "DELETE" });
export const copyCourse = (id: string) => request<{ id: string }>(coursePath(id) + "/copy", { method: "POST" });

export const createLesson = (courseId: string, title: string, type: LessonType, language?: string) =>
  request<{ id: string }>(coursePath(courseId) + "/lessons", json("POST", { title, type, language }));
export const lessonSource = (courseId: string, lessonId: string) => request<LessonSource>(lessonPath(courseId, lessonId));
export const saveLesson = (courseId: string, src: LessonSource) => request<void>(lessonPath(courseId, src.id), json("PUT", src));
export const deleteLesson = (courseId: string, lessonId: string) => request<void>(lessonPath(courseId, lessonId), { method: "DELETE" });
export const checkLesson = (courseId: string, lessonId: string) =>
  request<LessonCheckDetail>(lessonPath(courseId, lessonId) + "/check", { method: "POST" });

export const exportCourse = (courseId: string, path: string) =>
  request<{ path: string; checks: LessonCheck[] }>(coursePath(courseId) + "/export", json("POST", { path }));
export const importDojo = (path: string, replace = false) => request<ImportResult>("/studio/import", json("POST", { path, replace }));

// --- dialogs ---

export async function confirmDialog(text: string, title = "FreeKnowledge"): Promise<boolean> {
  if (!isTauri()) return window.confirm(text);
  return ask(text, { title, kind: "warning" });
}

export async function infoDialog(text: string, title = "FreeKnowledge"): Promise<void> {
  if (!isTauri()) return window.alert(text);
  await message(text, { title });
}

export async function pickDojoToOpen(): Promise<string | null> {
  if (!isTauri()) return window.prompt("Path to a .dojo file");
  const picked = await open({ multiple: false, directory: false, filters: [{ name: "FreeKnowledge course", extensions: ["dojo"] }] });
  return typeof picked === "string" ? picked : null;
}

export async function pickDojoToSave(defaultName: string): Promise<string | null> {
  if (!isTauri()) return window.prompt("Save .dojo file to (absolute path)", `/tmp/${defaultName}`);
  let path = await save({ defaultPath: defaultName, filters: [{ name: "FreeKnowledge course", extensions: ["dojo"] }] });
  if (path && !path.toLowerCase().endsWith(".dojo")) path += ".dojo";
  return path;
}

/**
 * Lets the user pick a .dojo and imports it, asking before replacing an
 * existing course. Returns the result, or null if cancelled.
 */
export async function importWithPrompts(): Promise<ImportResult | null> {
  const path = await pickDojoToOpen();
  if (!path) return null;
  try {
    return await importDojo(path);
  } catch (e) {
    if (e instanceof EngineError && e.status === 409) {
      const replace = await confirmDialog(
        `You already have a course named "${e.body.title ?? e.body.id}". Replace it with the imported version? Your current copy will be deleted.`,
      );
      return replace ? importDojo(path, true) : null;
    }
    throw e;
  }
}
