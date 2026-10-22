// FreeKnowledge node:test reporter. Appends one JSON record per test to
// $FK_RESULTS; it prints nothing, so the terminal shows only program output.
import { appendFileSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { inspect } from "node:util";

const results = process.env.FK_RESULTS;
const TEST_FILE = "solution_test.js";
const MAX_VALUE = 2000; // characters of input/expected/actual to show

function message(error) {
  const cause = error?.cause ?? error;
  if (!cause) return "";
  return String(cause.message ?? cause);
}

// --- structured failure details ---

// Equality assertions, by the operator node:assert records on the error.
const EQUALITY = new Set(["strictEqual", "deepStrictEqual", "equal", "deepEqual", "partialDeepStrictEqual"]);

function show(value) {
  const text = inspect(value, { depth: 6, breakLength: 72, maxArrayLength: 100, maxStringLength: MAX_VALUE });
  return text.length <= MAX_VALUE ? text : text.slice(0, MAX_VALUE) + "…";
}

// details returns input/expected/actual for a failed equality assertion, or
// nothing when the failure isn't one (a thrown error, assert.throws, …).
function details(error) {
  const cause = error?.cause ?? error;
  if (cause?.code !== "ERR_ASSERTION") return {};
  const op = cause.operator;
  // assert.ok(x) records operator "=="; it's only a comparison for booleans.
  const isOk = op === "==" && cause.expected === true && typeof cause.actual === "boolean";
  if (!EQUALITY.has(op) && !isOk) return {};
  const out = {};
  const input = inputFrom(cause.stack);
  if (input) out.input = input;
  out.expected = show(cause.expected);
  out.actual = show(cause.actual);
  return out;
}

// inputFrom finds the assertion in the test file from the stack and returns
// its first argument's source when that argument is a function call, e.g.
// `sum([1, 2, 3])` from `assert.equal(sum([1, 2, 3]), 6)`.
function inputFrom(stack) {
  const frame = String(stack ?? "")
    .split("\n")
    .map((l) => l.match(/\((.+):(\d+):(\d+)\)$/) ?? l.match(/at (.+):(\d+):(\d+)$/))
    .find((m) => m && m[1].endsWith("/" + TEST_FILE));
  if (!frame) return undefined;
  let source;
  try {
    const path = frame[1].startsWith("file:") ? fileURLToPath(frame[1]) : frame[1];
    source = readFileSync(path, "utf8");
  } catch {
    return undefined;
  }
  const lines = source.split("\n");
  const line = Number(frame[2]) - 1;
  if (line >= lines.length) return undefined;
  // The column points at the method name (`equal` in assert.equal).
  let pos = lines.slice(0, line).reduce((n, l) => n + l.length + 1, 0) + Number(frame[3]) - 1;
  pos = source.indexOf("(", pos);
  if (pos < 0) return undefined;
  const args = splitArgs(source, pos);
  const first = args?.[0]?.trim().replace(/^await\s+/, "");
  if (!first || !isCall(first)) return undefined;
  const text = first.replace(/\s*\n\s*/g, " ");
  return text.length <= MAX_VALUE ? text : text.slice(0, MAX_VALUE) + "…";
}

// isCall reports whether s is a single call like f(...) or obj.m(...),
// where the final ")" closes the first "(".
function isCall(s) {
  const m = s.match(/^[\w$]+(?:\s*\.\s*[\w$]+)*\s*\(/);
  if (!m || !s.endsWith(")")) return false;
  const args = splitArgs(s, m[0].length - 1);
  return args !== undefined && args.end === s.length - 1;
}

// splitArgs splits the parenthesized list starting at src[open] into its
// top-level arguments, skipping over strings, template literals and nested
// brackets. The returned array's `end` is the index of the closing ")".
function splitArgs(src, open) {
  const args = [];
  const closers = { "(": ")", "[": "]", "{": "}" };
  const stack = [];
  let start = open + 1;
  for (let i = open; i < src.length; i++) {
    const c = src[i];
    if (c === '"' || c === "'" || c === "`") {
      for (i++; i < src.length && src[i] !== c; i++) if (src[i] === "\\") i++;
    } else if (c === "/" && src[i + 1] === "/") {
      i = src.indexOf("\n", i);
      if (i < 0) return undefined;
    } else if (closers[c]) {
      stack.push(closers[c]);
    } else if (c === ")" || c === "]" || c === "}") {
      if (stack.pop() !== c) return undefined;
      if (stack.length === 0) {
        const last = src.slice(start, i);
        if (last.trim()) args.push(last);
        args.end = i;
        return args;
      }
    } else if (c === "," && stack.length === 1) {
      args.push(src.slice(start, i));
      start = i + 1;
    }
  }
  return undefined;
}

export default async function* reporter(source) {
  for await (const event of source) {
    if (event.type !== "test:pass" && event.type !== "test:fail") continue;
    const d = event.data;
    if (d.details?.type === "suite") continue;
    const status = d.skip || d.todo ? "skip" : event.type === "test:pass" ? "pass" : "fail";
    const record = {
      name: d.name,
      status,
      message: status === "fail" ? message(d.details?.error) : "",
      durationMs: Math.round(d.details?.duration_ms ?? 0),
      ...(status === "fail" ? safely(() => details(d.details?.error)) : {}),
    };
    appendFileSync(results, JSON.stringify(record) + "\n");
  }
}

// Reporting details must never lose the test's result.
function safely(fn) {
  try {
    return fn();
  } catch {
    return {};
  }
}
