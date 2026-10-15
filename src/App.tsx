import { useEffect, useState } from "react";
import { Home } from "./components/Home";
import { Workspace } from "./components/Workspace";
import * as engine from "./lib/engine";

type Route = { view: "home" } | { view: "lesson"; courseId: string; lessonId: string };
type LessonRef = { courseId: string; lessonId: string };

const LAST_LESSON_KEY = "fk:lastLesson";

function loadLastLesson(): LessonRef | undefined {
  try {
    const raw = localStorage.getItem(LAST_LESSON_KEY);
    return raw ? JSON.parse(raw) : undefined;
  } catch {
    return undefined;
  }
}

export default function App() {
  const [status, setStatus] = useState<"connecting" | "ok" | "down">("connecting");
  const [error, setError] = useState("");
  const [route, setRoute] = useState<Route>({ view: "home" });
  const [lastLesson, setLastLesson] = useState(loadLastLesson);

  useEffect(() => {
    engine
      .waitForEngine()
      .then(() => setStatus("ok"))
      .catch((e) => {
        setStatus("down");
        setError(String(e));
      });
  }, []);

  const openLesson = (courseId: string, lessonId: string) => {
    setRoute({ view: "lesson", courseId, lessonId });
    setLastLesson({ courseId, lessonId });
    try {
      localStorage.setItem(LAST_LESSON_KEY, JSON.stringify({ courseId, lessonId }));
    } catch {
      // Remembering the last lesson is a convenience; ignore storage failures.
    }
  };

  if (status !== "ok") {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center">
        {status === "connecting" ? (
          <p className="text-sm text-zinc-500">Starting engine…</p>
        ) : (
          <div className="max-w-md">
            <p className="mb-2 font-medium text-red-400">Couldn't reach the FreeKnowledge engine.</p>
            <p className="text-sm text-zinc-400">{error}</p>
            <p className="mt-4 text-xs text-zinc-500">Check the terminal running the app for [engine] errors, then restart it.</p>
          </div>
        )}
      </div>
    );
  }

  if (route.view === "lesson") {
    return (
      <Workspace
        courseId={route.courseId}
        lessonId={route.lessonId}
        onOpenLesson={(lessonId) => openLesson(route.courseId, lessonId)}
        onHome={() => setRoute({ view: "home" })}
      />
    );
  }
  return <Home lastLesson={lastLesson} onOpen={openLesson} />;
}
