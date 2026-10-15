import { useState } from "react";
import type { GradeResult } from "../../lib/engine";

interface Props {
  options: string[];
  /** The learner's last submitted answer, if any. */
  initialAnswer?: number;
  completed: boolean;
  onSubmit: (answer: number) => Promise<GradeResult>;
  onNext?: () => void;
}

const LETTERS = "ABCDEFGHIJ";

export function QuizPanel({ options, initialAnswer, completed, onSubmit, onNext }: Props) {
  const [selected, setSelected] = useState<number | undefined>(initialAnswer);
  const [result, setResult] = useState<GradeResult>();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>();

  const submit = async () => {
    if (selected === undefined || submitting) return;
    setSubmitting(true);
    setError(undefined);
    try {
      setResult(await onSubmit(selected));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const choose = (i: number) => {
    setSelected(i);
    setResult(undefined); // a new choice clears the old verdict
  };

  const verdict = result && (result.passed ? "right" : "wrong");

  return (
    <div className="h-full overflow-auto bg-zinc-950">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="mx-auto max-w-xl px-6 py-8"
      >
        <fieldset>
          <legend className="mb-4 text-sm font-medium tracking-wide text-zinc-400 uppercase">Choose one answer</legend>
          <div className="space-y-2">
            {options.map((option, i) => {
              const isSelected = selected === i;
              const tone =
                isSelected && verdict === "right"
                  ? "border-emerald-600 bg-emerald-950/50"
                  : isSelected && verdict === "wrong"
                    ? "border-red-700 bg-red-950/40"
                    : isSelected
                      ? "border-indigo-500 bg-indigo-950/40"
                      : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-600";
              return (
                <label key={i} className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${tone}`}>
                  <input type="radio" name="answer" value={i} checked={isSelected} onChange={() => choose(i)} className="sr-only" />
                  <span
                    className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                      isSelected ? "border-transparent bg-indigo-600 text-white" : "border-zinc-600 text-zinc-400"
                    }`}
                  >
                    {LETTERS[i] ?? i + 1}
                  </span>
                  <span className="text-zinc-100">{option}</span>
                </label>
              );
            })}
          </div>
        </fieldset>

        <div className="mt-6 flex items-center gap-3">
          <button
            type="submit"
            disabled={selected === undefined || submitting}
            className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
          >
            {submitting ? "Checking…" : "Submit Answer"}
          </button>
          {completed && !result && <span className="text-sm text-emerald-400">✓ You've answered this correctly before</span>}
        </div>

        {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        {verdict === "right" && (
          <div className="mt-5 flex items-center justify-between gap-3 rounded border border-emerald-800 bg-emerald-950/50 px-4 py-3">
            <span className="font-medium text-emerald-300">Correct!</span>
            {onNext && (
              <button type="button" onClick={onNext} className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium hover:bg-emerald-500">
                Next lesson →
              </button>
            )}
          </div>
        )}
        {verdict === "wrong" && (
          <p className="mt-5 rounded border border-red-900 bg-red-950/40 px-4 py-3 text-red-200">Not quite. Try another answer.</p>
        )}
      </form>
    </div>
  );
}
