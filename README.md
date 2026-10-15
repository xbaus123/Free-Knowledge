# FreeKnowledge

A free, open-source, offline-first desktop app for learning programming, systems engineering, and system design. Lessons run entirely on your machine using the compilers and runtimes you already have installed. No cloud sandboxes, accounts, or internet connection required.

> **Status:** early. The app shell, the Go engine, code execution, and the course loader and grader work. The lesson workspace UI, Creator Studio, and system design sandbox are next.

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

- `src/`: React frontend. `src/lib/engine.ts` is the engine client.
- `src-tauri/`: Rust shell. It starts the engine with a random per-launch token and gives that token to the webview through the `engine_info` command.
- `sidecar-go/`: the engine. `internal/runner` runs code, `internal/course` reads course packs, `internal/grader` runs hidden tests, and `internal/server` handles HTTP/WS, auth, and CORS.
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

See `courses/getting-started` for one example of each. In development the app reads `courses/` live; user courses go in the app data folder (`~/Library/Application Support/dev.freeknowledge.app/courses` on macOS).

## Development

Requirements: Node 20+, Rust (stable), Go 1.22+. Install whichever language toolchains you want to run code in.

```bash
npm install
npm run tauri dev       # builds the engine, then starts the app
npm run test:sidecar    # Go engine tests
npm run tauri build     # release bundle
```

To run the engine on its own:

```bash
cd sidecar-go && FK_ENGINE_TOKEN=dev FK_BUNDLED_COURSES=../courses go run . -no-stdin-watchdog
```

## License

[MIT](LICENSE)
