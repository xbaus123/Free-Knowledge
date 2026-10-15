# FreeKnowledge

A free, open-source, offline-first desktop app for learning programming, systems engineering, and system design. Lessons run entirely on your machine using the compilers and runtimes you already have installed. No cloud sandboxes, accounts, or internet connection required.

> **Status:** early. You can take courses end to end (lesson reader, code editor, hidden-test grading, saved progress) and write your own in Creator Studio, then share them as `.dojo` files. System design lessons (draw an architecture, then simulate traffic through it) are in progress; the AI tutor is next.

## Architecture

```
┌────────────── Tauri v2 (Rust) ──────────────┐
│  React + TS + Tailwind webview              │
│      │  HTTP / WebSocket (bearer token)     │
│      ▼                                      │
│  Go engine sidecar  ── 127.0.0.1:14200      │
│   • runs code in temp workspaces            │
│   • per-run timeouts, process-group kill    │
│   • exits when Tauri's stdin pipe closes    │
└─────────────────────────────────────────────┘
```

- `src/`: React frontend. `src/lib/engine.ts` is the engine client; `src/components/` has the home screen and lesson workspace.
- `src-tauri/`: Rust shell. It starts the engine with a random per-launch token and gives that token to the webview through the `engine_info` command.
- `sidecar-go/`: the engine. `internal/runner` runs code, `internal/course` reads course packs, `internal/grader` runs hidden tests, `internal/progress` stores progress in SQLite, `internal/studio` edits courses and reads/writes `.dojo` files, `internal/simulator` runs system design traffic simulations, and `internal/server` handles HTTP/WS, auth, and CORS.
- `courses/`: course packs bundled with the app.
- `scripts/build-sidecar.mjs`: compiles the engine to `src-tauri/binaries/engine-<target-triple>`.

### Engine API

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | `{status, version}` |
| GET | `/runtimes` | token | Supported languages and whether each toolchain is installed |
| POST | `/run` | token | `{language, code, stdin?, timeoutMs?}` → `{phase, exitCode, stdout, stderr, timedOut, truncated, durationMs}` |
| GET | `/courses` | token | All courses (user courses override bundled ones with the same ID) |
| GET | `/courses/{course}` | token | One course and its lesson list |
| GET | `/courses/{course}/lessons/{lesson}` | token | Lesson markdown and starter code (never the tests) |
| POST | `/courses/{course}/lessons/{lesson}/submit` | token | `{code}` → `{passed, tests: [{name, status, message, durationMs}], stdout, stderr, …}` |
| POST | `/courses/{course}/lessons/{lesson}/validate` | token | Grades the lesson's `reference.*` solution, so authors can check their tests |
| GET | `/progress` | token | Streak, lessons completed, and per-lesson progress for every course |
| GET | `/courses/{course}/lessons/{lesson}/progress` | token | Saved code, attempts, and completion for one lesson |
| PUT / DELETE | `/courses/{course}/lessons/{lesson}/progress/code` | token | Autosave `{code}`, or reset to the starter |
| POST | `/simulate` | token | `{course?, lesson?, graph: {nodes, edges}}` → `{passed, message, issues, metrics, nodes}`; with a lesson, its targets apply and progress is recorded |
| POST, PUT, DELETE | `/studio/...` | token | Creator Studio: create and edit courses and lessons (user courses only), `check` a lesson, `export` a course to a `.dojo` path, `import` one |
| GET | `/ws/run?token=…` | token | Send `{"type":"run",…}` or `{"type":"submit","course","lesson","code"}`; receive streamed `output` messages, then a `result` or `grade` message. Send `{"type":"cancel"}` to stop. |

Supported languages: Python, JavaScript (Node), Go, C (gcc), Rust (rustc).

## Writing a course

A course is a folder of lesson folders. The folder names are the IDs.

```
courses/my-course/
  course.json            {"title", "description", "author", "version", "language"?, "lessons"?: [ids]}
  01-first-lesson/
    lesson.md            instructions (the first "# " heading is the default title)
    config.json          optional: {"title", "language", "timeoutMs"}
    starter.py           code the learner starts from
    solution_test.py     hidden tests
    reference.py         your solution; `validate` checks that it passes
```

Lessons are ordered by `course.json`'s `lessons` list, or by folder name if it's absent. The learner's code is saved as `solution.<ext>` next to the tests. Tests use only each language's standard tooling:

| Language | Tests | Importing the learner's code |
|---|---|---|
| Python | `unittest` (docstrings become test names) | `from solution import greet` |
| JavaScript | `node:test` + `node:assert` (ES modules) | `import { sum } from "./solution.js"` |
| Go | `testing` (subtests are reported individually) | same package |
| C | `#include "fk_test.h"`, then `TEST(name) { EXPECT_EQ_INT(a, b); }` | declare the prototype; don't write `main` |
| Rust | `#[test]` functions | `use super::*;` |

See `courses/getting-started` for one example of each.

### Article and quiz lessons

For a reading-only lesson, set `"type": "article"` in `config.json`; the lesson is just `lesson.md`, and learners finish it with **Mark Complete**.

For a multiple-choice question, set `"type": "quiz"` and list the choices in `config.json`'s `"options"`. Put the question in `lesson.md` and the zero-based answer in `solution.json`: `{"correct_index": 0}`. Learners submit `{"answer": N}` to the lesson's `submit` endpoint. A wrong answer doesn't reveal the right one, so learners can try again. True/false questions are a quiz with two options.

### System design lessons

Set `"type": "system-design"` in a lesson's `config.json`, with `maxLatencyMs` as the p99 target. Instead of code files, the lesson has `starter.json` (the diagram learners start from) and `solution.json` (a reference design that must pass). Both are React Flow graphs: nodes of type `client`, `loadBalancer`, `server`, or `database`, plus edges. **Simulate Traffic** sends 1,000 requests over one second through the learner's diagram. Grading is by behavior (overloaded servers, p99 latency, unanswered requests), so any design with enough capacity passes. See `courses/system-design`. The Studio can check and export these lessons but can't edit their diagrams yet. In development the app reads `courses/` live; user courses go in the app data folder (`~/Library/Application Support/dev.freeknowledge.app/courses` on macOS).

## Creator Studio and `.dojo` files

Open **Creator Studio** from the home screen to write courses without touching the file system. New lessons start from a working example in the language you pick. **Check lesson** runs your reference solution (it must pass) and the starter code (it should fail) against your tests. **Export .dojo** checks every lesson and refuses to export until each reference solution passes. Bundled courses are read-only; use **Make an editable copy** to remix one.

A `.dojo` file is a zip of one course folder plus a `dojo.json` manifest (`{"format": 1, "id": "<course-id>", ...}`). It includes reference solutions. Importing accepts only the files in the course layout above, enforces size limits, and never runs anything. Imported courses go in your user course folder; a course with the same ID asks before replacing.

> Lesson tests run on your computer when you submit, like any code you download. Only import courses from people you trust.

## Development

Requirements: Node 20+, Rust (stable), Go 1.22+. Install whichever language toolchains you want to run code in.

```bash
npm install
npm run tauri dev       # builds the engine, then starts the app
npm run test:sidecar    # Go engine tests
npm run tauri build     # release bundle
```

To work on the UI in a regular browser (faster reloads, browser dev tools), run these in two terminals and open http://localhost:1430 (they use their own ports, so they can run alongside `npm run tauri dev`):

```bash
npm run dev:engine   # engine on :14210 with token "dev"; progress and your courses in .dev-data/
npm run dev:web      # Vite with the matching token
```

Progress is stored in `progress.db` in the app data folder (`~/Library/Application Support/dev.freeknowledge.app/` on macOS).

## License

[MIT](LICENSE)
