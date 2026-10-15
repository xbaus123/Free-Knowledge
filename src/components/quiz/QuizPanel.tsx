import { useState } from "react";
import type { GradeResult, QuizQuestion } from "../../lib/engine";

interface Props {
  questions: QuizQuestion[];
  /** The learner's last submitted answers, if any. */
  initialAnswers?: number[];
  completed: boolean;
  onSubmit: (answers: number[]) => Promise<GradeResult>;
  onNext?: () => void;
}

const LETTERS = "ABCDEFGHIJ";

export function QuizPanel({ questions, initialAnswers, completed, onSubmit, onNext }: Props) {
  const [answers, setAnswers] = useState<(number | undefined)[]>(() => questions.map((_, i) => initialAnswers?.[i]));
  const [result, setResult] = useState<GradeResult>();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>();

  const allAnswered = answers.every((a) => a !== undefined);
  const multiple = questions.length > 1;

  const submit = async () => {
    if (!allAnswered || submitting) return;
    setSubmitting(true);
    setError(undefined);
    try {
      setResult(await onSubmit(answers as number[]));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const choose = (q: number, option: number) => {
    setAnswers((a) => a.map((v, i) => (i === q ? option : v)));
    // A new choice clears that question's verdict; others keep theirs.
    setResult((r) => r && { ...r, passed: false, tests: r.tests.map((t, i) => (i === q ? { ...t, status: "skip", message: "" } : t)) });
  };

  const correctCount = result?.tests.filter((t) => t.status === "pass").length ?? 0;

  return (
    <div className="h-full overflow-auto bg-zinc-950">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="mx-auto max-w-xl space-y-8 px-6 py-8"
      >
        {questions.map((q, qi) => {
          const verdict = result?.tests[qi]?.status;
          return (
            <fieldset key={qi}>
              <legend className="mb-3">
                {multiple && <span className="mb-1 block text-xs font-medium tracking-wide text-zinc-500 uppercase">Question {qi + 1}</span>}
                <span className={q.prompt ? "font-medium text-zinc-100" : "text-sm font-medium tracking-wide text-zinc-400 uppercase"}>
                  {q.prompt || "Choose one answer"}
                </span>
              </legend>
              <div className="space-y-2">
                {q.options.map((option, oi) => {
                  const isSelected = answers[qi] === oi;
                  const tone =
                    isSelected && verdict === "pass"
                      ? "border-emerald-600 bg-emerald-950/50"
                      : isSelected && verdict === "fail"
                        ? "border-red-700 bg-red-950/40"
                        : isSelected
                          ? "border-indigo-500 bg-indigo-950/40"
                          : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-600";
                  return (
                    <label key={oi} className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${tone}`}>
                      <input type="radio" name={`q${qi}`} checked={isSelected} onChange={() => choose(qi, oi)} className="sr-only" />
                      <span
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                          isSelected ? "border-transparent bg-indigo-600 text-white" : "border-zinc-600 text-zinc-400"
                        }`}
                      >
                        {LETTERS[oi] ?? oi + 1}
                      </span>
                      <span className="text-zinc-100">{option}</span>
                    </label>
                  );
                })}
              </div>
              {verdict === "pass" && (
                <div className="mt-3 rounded border border-emerald-900 bg-emerald-950/40 px-4 py-3 text-sm">
                  <span className="font-medium text-emerald-300">Correct!</span>
                  {result?.tests[qi].message && <p className="mt-1 text-emerald-100/80">{result.tests[qi].message}</p>}
                </div>
              )}
              {verdict === "fail" && (
                <p className="mt-3 rounded border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">Not quite. Try another answer.</p>
              )}
            </fieldset>
          );
        })}

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={!allAnswered || submitting}
            className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
          >
            {submitting ? "Checking…" : multiple ? "Submit Answers" : "Submit Answer"}
          </button>
          {multiple && !allAnswered && <span className="text-sm text-zinc-500">Answer every question to submit.</span>}
          {result && multiple && !result.passed && (
            <span className="text-sm text-zinc-400">
              {correctCount} of {questions.length} correct
            </span>
          )}
          {completed && !result && <span className="text-sm text-emerald-400">✓ You've completed this quiz before</span>}
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}
        {result?.passed && (
          <div className="flex items-center justify-between gap-3 rounded border border-emerald-800 bg-emerald-950/50 px-4 py-3">
            <span className="font-medium text-emerald-300">{multiple ? "All correct. Nice work!" : "Nice work!"}</span>
            {onNext && (
              <button type="button" onClick={onNext} className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium hover:bg-emerald-500">
                Next lesson →
              </button>
            )}
          </div>
        )}
      </form>
    </div>
  );
}
