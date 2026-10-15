import { useEffect, useState } from "react";
import * as engine from "../lib/engine";

interface Props {
  lastLesson?: { courseId: string; lessonId: string };
  onOpen: (courseId: string, lessonId: string) => void;
}

export function Home({ lastLesson, onOpen }: Props) {
  const [courses, setCourses] = useState<engine.Course[]>();
  const [progress, setProgress] = useState<engine.Progress>();
  const [runtimes, setRuntimes] = useState<engine.RuntimeInfo[]>([]);
  const [error, setError] = useState<string>();

  useEffect(() => {
    Promise.all([engine.courses(), engine.progress(), engine.runtimes()])
      .then(([c, p, r]) => {
        setCourses(c);
        setProgress(p);
        setRuntimes(r);
      })
      .catch((e) => setError(String(e)));
  }, []);

  const done = (courseId: string, lessonId: string) => !!progress?.courses[courseId]?.[lessonId]?.completed;

  const openCourse = (c: engine.Course) => {
    const target = c.lessons.find((l) => !done(c.id, l.id)) ?? c.lessons[0];
    if (target) onOpen(c.id, target.id);
  };

  const resume = lastLesson && courses?.find((c) => c.id === lastLesson.courseId);
  const resumeLesson = resume?.lessons.find((l) => l.id === lastLesson?.lessonId);
  const missing = runtimes.filter((r) => !r.available);

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">FreeKnowledge</h1>
            <p className="text-sm text-zinc-400">Learn to code on your own machine, fully offline.</p>
          </div>
          {progress && (
            <div className="flex gap-3 text-sm">
              <Stat label="day streak" value={progress.stats.currentStreak} accent={progress.stats.currentStreak > 0 ? "text-amber-300" : undefined} />
              <Stat label="lessons done" value={progress.stats.completedLessons} />
            </div>
          )}
        </header>

        {error && <p className="mb-6 rounded border border-red-900 bg-red-950/40 p-3 text-sm text-red-300">{error}</p>}

        {resume && resumeLesson && (
          <button
            onClick={() => onOpen(resume.id, resumeLesson.id)}
            className="mb-8 flex w-full items-center justify-between rounded-lg border border-indigo-800 bg-indigo-950/40 px-4 py-3 text-left hover:border-indigo-600"
          >
            <span>
              <span className="block text-xs text-indigo-300">Continue where you left off</span>
              <span className="font-medium">
                {resume.title} · {resumeLesson.title}
              </span>
            </span>
            <span className="text-indigo-300">→</span>
          </button>
        )}

        <h2 className="mb-3 text-sm font-medium tracking-wide text-zinc-400 uppercase">Courses</h2>
        {courses === undefined && !error && <p className="text-sm text-zinc-500">Loading…</p>}
        {courses?.length === 0 && (
          <p className="text-sm text-zinc-500">No courses found. Add course folders to the courses directory to get started.</p>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          {courses?.map((c) => {
            const completed = c.lessons.filter((l) => done(c.id, l.id)).length;
            const pct = c.lessons.length ? Math.round((completed / c.lessons.length) * 100) : 0;
            return (
              <div key={c.id} className="flex flex-col rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
                <div className="mb-1 flex items-start justify-between gap-2">
                  <h3 className="font-medium">{c.title}</h3>
                  {c.source === "user" && <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400 uppercase">Yours</span>}
                </div>
                <p className="mb-4 text-sm text-zinc-400">{c.description}</p>
                {c.problems && c.problems.length > 0 && (
                  <p className="mb-3 text-xs text-amber-400" title={c.problems.join("\n")}>
                    ⚠ {c.problems.length} problem{c.problems.length > 1 ? "s" : ""} loading this course
                  </p>
                )}
                <ol className="mb-4 space-y-1 text-sm">
                  {c.lessons.map((l, i) => (
                    <li key={l.id}>
                      <button
                        onClick={() => onOpen(c.id, l.id)}
                        className="flex w-full items-center gap-2 rounded px-1.5 py-0.5 text-left text-zinc-300 hover:bg-zinc-800"
                      >
                        <span className={`w-4 text-center ${done(c.id, l.id) ? "text-emerald-400" : "text-zinc-600"}`}>
                          {done(c.id, l.id) ? "✓" : i + 1}
                        </span>
                        <span className="truncate">{l.title}</span>
                      </button>
                    </li>
                  ))}
                </ol>
                <div className="mt-auto flex items-center gap-3">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-800">
                    <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="w-20 text-right text-xs text-zinc-500">
                    {completed}/{c.lessons.length} done
                  </span>
                  <button
                    onClick={() => openCourse(c)}
                    disabled={c.lessons.length === 0}
                    className="rounded bg-indigo-600 px-3 py-1 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
                  >
                    {completed === 0 ? "Start" : completed === c.lessons.length ? "Review" : "Continue"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {missing.length > 0 && (
          <p className="mt-8 text-xs text-zinc-500">
            Not installed: {missing.map((r) => `${r.name} (${r.requires})`).join(", ")}. Lessons in these languages can't run until
            they're installed.
          </p>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: number; accent?: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-4 py-2 text-center">
      <div className={`text-xl font-semibold ${accent ?? "text-zinc-100"}`}>{value}</div>
      <div className="text-xs text-zinc-500">{label}</div>
    </div>
  );
}
