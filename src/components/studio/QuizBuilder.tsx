import type { QuestionSource } from "../../lib/studio";
import { inputClass } from "./StudioHome";

interface Props {
  questions: QuestionSource[];
  onChange: (questions: QuestionSource[]) => void;
}

const LETTERS = "ABCDEFGHIJ";
const MAX_OPTIONS = 10;

/** Edits quiz questions: prompt, options, which one is correct, and the explanation. */
export function QuizBuilder({ questions, onChange }: Props) {
  const set = (i: number, patch: Partial<QuestionSource>) => onChange(questions.map((q, j) => (j === i ? { ...q, ...patch } : q)));
  const remove = (i: number) => onChange(questions.filter((_, j) => j !== i));
  const move = (i: number, delta: number) => {
    const next = [...questions];
    [next[i], next[i + delta]] = [next[i + delta], next[i]];
    onChange(next);
  };
  const add = () => onChange([...questions, { prompt: "", options: ["", ""], correctIndex: 0, explanation: "" }]);

  return (
    <div className="h-full overflow-auto">
      <div className="mx-auto max-w-3xl space-y-4 p-6">
        <p className="text-xs text-zinc-500">
          Select the circle next to the correct answer. Learners see whether each answer is right, and the explanation appears only after they get
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

            <label className="mb-3 block">
              <span className="mb-1 block text-xs text-zinc-400">Question</span>
              <textarea
                value={q.prompt}
                onChange={(e) => set(i, { prompt: e.target.value })}
                rows={2}
                placeholder={questions.length === 1 ? "Leave empty if the question is in the intro text" : "What do you want to ask?"}
                className={`${inputClass} resize-y`}
              />
            </label>

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
                    onChange={(e) => set(i, { options: q.options.map((o, j) => (j === oi ? e.target.value : o)) })}
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
        <button type="button" onClick={add} className="w-full rounded-lg border border-dashed border-zinc-700 py-2.5 text-sm text-indigo-300 hover:bg-zinc-900">
          + Add question
        </button>
      </div>
    </div>
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
