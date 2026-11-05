import { useEffect, useRef, useState } from "react";
import type { GradeResult, QuizQuestion, QuizResponse, TestResult } from "../../lib/engine";

interface Props {
  questions: QuizQuestion[];
  /** The learner's last submitted answers, if any. */
  initialAnswers?: QuizResponse[];
  completed: boolean;
  onSubmit: (answers: QuizResponse[]) => Promise<GradeResult>;
  /**
   * Checks one answer as soon as it's chosen (quizzes with immediate
   * feedback). Once every answer is right, the quiz is submitted.
   */
  onCheck?: (question: number, answer: QuizResponse) => Promise<TestResult>;
  onNext?: () => void;
}

const LETTERS = "ABCDEFGHIJ";

const isWritten = (q: QuizQuestion) => q.type === "written";
/** Whether a is a usable answer to q (written answers need some text). */
const answered = (q: QuizQuestion, a: QuizResponse | undefined) => (isWritten(q) ? typeof a === "string" && a.trim() !== "" : typeof a === "number");

export function QuizPanel({ questions, initialAnswers, completed, onSubmit, onCheck, onNext }: Props) {
  const immediate = !!onCheck;
  // Saved answers that don't fit the question (it changed type since) are dropped.
  const [answers, setAnswers] = useState<(QuizResponse | undefined)[]>(() =>
    questions.map((q, i) => {
      const a = initialAnswers?.[i];
      return (isWritten(q) ? typeof a === "string" : typeof a === "number") ? a : undefined;
    }),
  );
  // Per-question verdicts: from the last submit, or from each check.
  const [verdicts, setVerdicts] = useState<(TestResult | undefined)[]>(() => questions.map(() => undefined));
  // Immediate mode: wrong options already tried, per question.
  const [tried, setTried] = useState<Set<number>[]>(() => questions.map(() => new Set()));
  const [checking, setChecking] = useState<Set<number>>(new Set());
  const [passed, setPassed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>();
  const submitted = useRef(false);

  const allAnswered = questions.every((q, i) => answered(q, answers[i]));
  const multiple = questions.length > 1;
  const correctCount = verdicts.filter((v) => v?.status === "pass").length;

  const submit = async (list = answers) => {
    if (!questions.every((q, i) => answered(q, list[i])) || submitting) return;
    setSubmitting(true);
    setError(undefined);
    try {
      const res = await onSubmit(list as QuizResponse[]);
      setVerdicts(questions.map((_, i) => res.tests[i]));
      setPassed(res.passed);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  };

  const check = async (q: number, option: QuizResponse, restoring = false) => {
    if (!onCheck) return;
    setChecking((c) => new Set(c).add(q));
    setError(undefined);
    try {
      const verdict = await onCheck(q, option);
      setVerdicts((v) => v.map((x, i) => (i === q ? verdict : x)));
      if (verdict.status !== "pass" && !restoring && typeof option === "number")
        setTried((t) => t.map((s, i) => (i === q ? new Set(s).add(option) : s)));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setChecking((c) => {
        const next = new Set(c);
        next.delete(q);
        return next;
      });
    }
  };

  // Immediate mode: show verdicts for answers restored from last time.
  useEffect(() => {
    if (!immediate) return;
    answers.forEach((a, i) => answered(questions[i], a) && check(i, a as QuizResponse, true));
    // Only on open.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Immediate mode: once every answer is right, record the completed quiz.
  useEffect(() => {
    if (!immediate || correctCount !== questions.length || questions.length === 0) return;
    setPassed(true);
    if (!completed && !submitted.current) {
      submitted.current = true;
      onSubmit(answers as QuizResponse[]).catch((e) => setError(e instanceof Error ? e.message : String(e)));
    }
  }, [immediate, correctCount, questions.length, completed, answers, onSubmit]);

  /** Typing a written answer: clears its verdict; it's checked on Enter or the Check button. */
  const type = (q: number, text: string) => {
    if (immediate && (verdicts[q]?.status === "pass" || checking.has(q))) return;
    setAnswers((a) => a.map((v, i) => (i === q ? text : v)));
    setVerdicts((v) => v.map((x, i) => (i === q ? undefined : x)));
    if (!immediate) setPassed(false);
  };

  const checkWritten = (q: number) => {
    const a = answers[q];
    if (!immediate || !answered(questions[q], a) || checking.has(q) || verdicts[q]?.status === "pass") return;
    check(q, a as QuizResponse);
  };

  const choose = (q: number, option: number) => {
    if (immediate && (verdicts[q]?.status === "pass" || checking.has(q))) return; // locked once right
    setAnswers((a) => a.map((v, i) => (i === q ? option : v)));
    if (immediate) {
      setVerdicts((v) => v.map((x, i) => (i === q ? undefined : x)));
      check(q, option);
      return;
    }
    // A new choice clears that question's verdict; others keep theirs.
    setVerdicts((v) => v.map((x, i) => (i === q ? undefined : x)));
    setPassed(false);
  };

  return (
    <div className="h-full overflow-auto bg-zinc-950">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (!immediate) submit();
        }}
        className="mx-auto max-w-xl space-y-8 px-6 py-8"
      >
        {immediate && (
          <p className="text-sm text-zinc-400">
            Each answer is checked as soon as you choose it
            {questions.some(isWritten) ? " (or press Enter after typing it)" : ""}. Get every question right to complete the quiz.
          </p>
        )}
        {questions.map((q, qi) => {
          const verdict = verdicts[qi]?.status;
          const locked = immediate && verdict === "pass";
          return (
            <fieldset key={qi} disabled={locked}>
              <legend className="mb-3">
                {multiple && <span className="mb-1 block text-xs font-medium tracking-wide text-zinc-500 uppercase">Question {qi + 1}</span>}
                <span className={q.prompt ? "font-medium text-zinc-100" : "text-sm font-medium tracking-wide text-zinc-400 uppercase"}>
                  {q.prompt || (isWritten(q) ? "Type your answer" : "Choose one answer")}
                </span>
              </legend>
              {isWritten(q) ? (
                <div className="flex gap-2">
                  <input
                    value={typeof answers[qi] === "string" ? (answers[qi] as string) : ""}
                    onChange={(e) => type(qi, e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && immediate) {
                        e.preventDefault();
                        checkWritten(qi);
                      }
                    }}
                    maxLength={2000}
                    placeholder="Type your answer"
                    aria-label={q.prompt || `Answer to question ${qi + 1}`}
                    autoComplete="off"
                    spellCheck={false}
                    className={`min-w-0 flex-1 rounded-lg border bg-zinc-900/50 px-4 py-3 text-zinc-100 outline-none placeholder:text-zinc-600 ${
                      verdict === "pass"
                        ? "border-emerald-600 bg-emerald-950/50"
                        : verdict === "fail"
                          ? "border-red-700 bg-red-950/40"
                          : "border-zinc-800 focus:border-indigo-500"
                    }`}
                  />
                  {immediate && !locked && (
                    <button
                      type="button"
                      onClick={() => checkWritten(qi)}
                      disabled={!answered(q, answers[qi]) || checking.has(qi)}
                      className="rounded-lg bg-indigo-600 px-4 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
                    >
                      Check
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  {(q.options ?? []).map((option, oi) => {
                    const isSelected = answers[qi] === oi;
                    const wrongBefore = tried[qi].has(oi) && !isSelected;
                    const tone =
                      isSelected && verdict === "pass"
                        ? "border-emerald-600 bg-emerald-950/50"
                        : isSelected && verdict === "fail"
                          ? "border-red-700 bg-red-950/40"
                          : isSelected
                            ? "border-indigo-500 bg-indigo-950/40"
                            : locked
                              ? "border-zinc-800 bg-zinc-900/30 opacity-50"
                              : wrongBefore
                                ? "border-zinc-800 bg-zinc-900/30 opacity-60 hover:border-zinc-600"
                                : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-600";
                    return (
                      <label
                        key={oi}
                        className={`flex items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${locked ? "cursor-default" : "cursor-pointer"} ${tone}`}
                      >
                        <input type="radio" name={`q${qi}`} checked={isSelected} onChange={() => choose(qi, oi)} className="sr-only" />
                        <span
                          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${
                            isSelected && verdict === "pass"
                              ? "border-transparent bg-emerald-600 text-white"
                              : isSelected && verdict === "fail"
                                ? "border-transparent bg-red-600 text-white"
                                : isSelected
                                  ? "border-transparent bg-indigo-600 text-white"
                                  : "border-zinc-600 text-zinc-400"
                          }`}
                        >
                          {isSelected && verdict === "pass"
                            ? "✓"
                            : (isSelected && verdict === "fail") || wrongBefore
                              ? "✗"
                              : ((q.type === "true_false" ? "TF"[oi] : LETTERS[oi]) ?? oi + 1)}
                        </span>
                        <span className={wrongBefore ? "text-zinc-400 line-through decoration-zinc-600" : "text-zinc-100"}>{option}</span>
                      </label>
                    );
                  })}
                </div>
              )}
              {checking.has(qi) && <p className="mt-3 text-sm text-zinc-500">Checking…</p>}
              {verdict === "pass" && (
                <div className="mt-3 rounded border border-emerald-900 bg-emerald-950/40 px-4 py-3 text-sm">
                  <span className="font-medium text-emerald-300">Correct!</span>
                  {verdicts[qi]?.message && <p className="mt-1 text-emerald-100/80">{verdicts[qi]?.message}</p>}
                </div>
              )}
              {verdict === "fail" && (
                <p className="mt-3 rounded border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-200">
                  Not quite. {isWritten(q) ? "Check your answer and try again." : "Try another answer."}
                </p>
              )}
            </fieldset>
          );
        })}

        {immediate ? (
          !passed && (
            <p className="text-sm text-zinc-400">
              {correctCount} of {questions.length} correct
            </p>
          )
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={!allAnswered || submitting}
              className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-40"
            >
              {submitting ? "Checking…" : multiple ? "Submit Answers" : "Submit Answer"}
            </button>
            {multiple && !allAnswered && <span className="text-sm text-zinc-500">Answer every question to submit.</span>}
            {verdicts.some(Boolean) && multiple && !passed && (
              <span className="text-sm text-zinc-400">
                {correctCount} of {questions.length} correct
              </span>
            )}
            {completed && !verdicts.some(Boolean) && <span className="text-sm text-emerald-400">✓ You've completed this quiz before</span>}
          </div>
        )}

        {error && <p className="text-sm text-red-400">{error}</p>}
        {passed && (
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
