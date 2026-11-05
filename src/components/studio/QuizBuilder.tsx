import type { QuestionSource, QuestionType } from "../../lib/studio";
import { inputClass } from "./StudioHome";

interface Props {
  questions: QuestionSource[];
  onChange: (questions: QuestionSource[]) => void;
}

const LETTERS = "ABCDEFGHIJ";
const MAX_OPTIONS = 10;
const MAX_ACCEPTED = 10;
const TRUE_FALSE = ["True", "False"];

const TYPES: { id: QuestionType; label: string }[] = [
  { id: "choice", label: "Multiple choice" },
  { id: "true_false", label: "True / false" },
  { id: "written", label: "Written answer" },
];

const typeOf = (q: QuestionSource): QuestionType => q.type ?? "choice";

/** What changes when a question switches type. Choice options are kept where they still make sense. */
function retype(q: QuestionSource, type: QuestionType): Partial<QuestionSource> {
  switch (type) {
    case "true_false":
      return {
        type,
        options: TRUE_FALSE,
        correctIndex: q.correctIndex === 1 ? 1 : 0,
      };
    case "written":
      return {
        type,
        acceptedAnswers: q.acceptedAnswers?.length ? q.acceptedAnswers : [""],
      };
    default: {
      const options = typeOf(q) === "written" && q.options.length < 2 ? ["", ""] : q.options;
      return {
        type,
        options,
        correctIndex: Math.min(q.correctIndex, options.length - 1),
      };
    }
  }
}

/** Edits quiz questions: prompt, options, which one is correct, and the explanation. */
export function QuizBuilder({ questions, onChange }: Props) {
  const set = (i: number, patch: Partial<QuestionSource>) => onChange(questions.map((q, j) => (j === i ? { ...q, ...patch } : q)));
  const remove = (i: number) => onChange(questions.filter((_, j) => j !== i));
  const move = (i: number, delta: number) => {
    const next = [...questions];
    [next[i], next[i + delta]] = [next[i + delta], next[i]];
    onChange(next);
  };
  const add = (type: QuestionType = "choice") =>
    onChange([
      ...questions,
      type === "true_false"
        ? {
            type,
            prompt: "",
            options: TRUE_FALSE,
            correctIndex: 0,
            explanation: "",
          }
        : type === "written"
          ? {
              type,
              prompt: "",
              options: [],
              correctIndex: 0,
              acceptedAnswers: [""],
              explanation: "",
            }
          : {
              type,
              prompt: "",
              options: ["", ""],
              correctIndex: 0,
              explanation: "",
            },
    ]);

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-3xl space-y-4 p-6">
        <p className="text-xs text-zinc-500">
          Pick a type for each question. For multiple choice and true/false, select the correct answer; for written answers, list every answer that
          should count (case and extra spaces are ignored). Learners see whether each answer is right, and the explanation appears only after they get
          it right.
        </p>
        {questions.map((q, i) => (
          <section key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-4">
            <div className="mb-3 flex items-center gap-2">
              <span className="text-xs font-medium tracking-wide text-zinc-400 uppercase">Question {i + 1}</span>
              <span className="ml-auto flex gap-1">
                <SmallButton label="Move up" disabled={i === 0} onClick={() => move(i, -1)}>
                  ↑
                </SmallButton>
                <SmallButton label="Move down" disabled={i === questions.length - 1} onClick={() => move(i, 1)}>
                  ↓
                </SmallButton>
                <SmallButton label="Delete question" disabled={questions.length === 1} onClick={() => remove(i)} danger>
                  Delete
                </SmallButton>
              </span>
            </div>

            <div role="radiogroup" aria-label={`Question ${i + 1} type`} className="mb-3 inline-flex rounded-md border border-zinc-800 p-0.5">
              {TYPES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  role="radio"
                  aria-checked={typeOf(q) === t.id}
                  onClick={() => typeOf(q) !== t.id && set(i, retype(q, t.id))}
                  className={`rounded px-2.5 py-1 text-xs ${typeOf(q) === t.id ? "bg-zinc-800 text-zinc-100" : "text-zinc-400 hover:text-zinc-200"}`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <label className="mb-3 block">
              <span className="mb-1 block text-xs text-zinc-400">{typeOf(q) === "true_false" ? "Statement" : "Question"}</span>
              <textarea
                value={q.prompt}
                onChange={(e) => set(i, { prompt: e.target.value })}
                rows={2}
                placeholder={
                  questions.length === 1
                    ? "Leave empty if the question is in the intro text"
                    : typeOf(q) === "true_false"
                      ? "A statement that is either true or false"
                      : "What do you want to ask?"
                }
                className={`${inputClass} resize-y`}
              />
            </label>

            {typeOf(q) === "true_false" ? (
              <>
                <span className="mb-1 block text-xs text-zinc-400">Correct answer</span>
                <div className="flex gap-2">
                  {TRUE_FALSE.map((label, oi) => (
                    <label
                      key={label}
                      className={`flex cursor-pointer items-center gap-2 rounded border px-3 py-1.5 text-sm ${
                        q.correctIndex === oi ? "border-emerald-700 text-zinc-100" : "border-zinc-800 text-zinc-400 hover:border-zinc-600"
                      }`}
                    >
                      <input
                        type="radio"
                        name={`correct-${i}`}
                        checked={q.correctIndex === oi}
                        onChange={() => set(i, { correctIndex: oi })}
                        className="h-4 w-4 accent-emerald-500"
                      />
                      {q.options[oi] || label}
                    </label>
                  ))}
                </div>
              </>
            ) : typeOf(q) === "written" ? (
              <AcceptedAnswers answers={q.acceptedAnswers ?? [""]} onChange={(acceptedAnswers) => set(i, { acceptedAnswers })} />
            ) : (
              <>
                <span className="mb-1 block text-xs text-zinc-400">Options</span>
                <div className="space-y-1.5">
                  {q.options.map((option, oi) => (
                    <div key={oi} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name={`correct-${i}`}
                        checked={q.correctIndex === oi}
                        onChange={() => set(i, { correctIndex: oi })}
                        title="Mark as the correct answer"
                        aria-label={`Option ${LETTERS[oi]} is correct`}
                        className="h-4 w-4 shrink-0 accent-emerald-500"
                      />
                      <span className="w-4 text-xs text-zinc-500">{LETTERS[oi]}</span>
                      <input
                        value={option}
                        onChange={(e) =>
                          set(i, {
                            options: q.options.map((o, j) => (j === oi ? e.target.value : o)),
                          })
                        }
                        placeholder={`Option ${LETTERS[oi]}`}
                        className={`${inputClass} ${q.correctIndex === oi ? "border-emerald-700" : ""}`}
                      />
                      <SmallButton
                        label="Remove option"
                        disabled={q.options.length <= 2}
                        onClick={() => {
                          const options = q.options.filter((_, j) => j !== oi);
                          // Keep the same option marked correct when an earlier one is removed.
                          const correctIndex = q.correctIndex === oi ? 0 : q.correctIndex > oi ? q.correctIndex - 1 : q.correctIndex;
                          set(i, { options, correctIndex });
                        }}
                      >
                        ✕
                      </SmallButton>
                    </div>
                  ))}
                </div>
                {q.options.length < MAX_OPTIONS && (
                  <button
                    type="button"
                    onClick={() => set(i, { options: [...q.options, ""] })}
                    className="mt-2 rounded px-2 py-1 text-xs text-indigo-300 hover:bg-zinc-800"
                  >
                    + Add option
                  </button>
                )}
              </>
            )}

            <label className="mt-3 block">
              <span className="mb-1 block text-xs text-zinc-400">Explanation (optional, shown after a correct answer)</span>
              <textarea
                value={q.explanation}
                onChange={(e) => set(i, { explanation: e.target.value })}
                rows={2}
                placeholder="Why is this the right answer?"
                className={`${inputClass} resize-y`}
              />
            </label>
          </section>
        ))}
        <div className="flex overflow-hidden rounded-lg border border-dashed border-zinc-700 text-sm text-indigo-300">
          {TYPES.map((t) => (
            <button key={t.id} type="button" onClick={() => add(t.id)} className="flex-1 py-2.5 hover:bg-zinc-900">
              + {t.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

/** The answers a written question accepts. */
function AcceptedAnswers({ answers, onChange }: { answers: string[]; onChange: (answers: string[]) => void }) {
  return (
    <>
      <span className="mb-1 block text-xs text-zinc-400">Accepted answers</span>
      <div className="space-y-1.5">
        {answers.map((answer, ai) => (
          <div key={ai} className="flex items-center gap-2">
            <input
              value={answer}
              onChange={(e) => onChange(answers.map((a, j) => (j === ai ? e.target.value : a)))}
              placeholder={ai === 0 ? "The right answer" : "Another way to write it"}
              aria-label={`Accepted answer ${ai + 1}`}
              className={`${inputClass} border-emerald-700`}
            />
            <SmallButton label="Remove accepted answer" disabled={answers.length <= 1} onClick={() => onChange(answers.filter((_, j) => j !== ai))}>
              ✕
            </SmallButton>
          </div>
        ))}
      </div>
      {answers.length < MAX_ACCEPTED && (
        <button type="button" onClick={() => onChange([...answers, ""])} className="mt-2 rounded px-2 py-1 text-xs text-indigo-300 hover:bg-zinc-900">
          + Add another accepted answer
        </button>
      )}
    </>
  );
}

function SmallButton({
  label,
  disabled,
  onClick,
  danger,
  children,
}: {
  label: string;
  disabled?: boolean;
  onClick: () => void;
  danger?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={onClick}
      className={`rounded px-1.5 py-1 text-xs text-zinc-500 hover:bg-zinc-800 disabled:invisible ${danger ? "hover:text-red-400" : "hover:text-zinc-200"}`}
    >
      {children}
    </button>
  );
}
