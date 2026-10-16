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
| GET, POST, DELETE | `/courses/{course}/lessons/{lesson}/telemetry`, `GET /telemetry` | token | Local learning insights (only for lessons with telemetry on) |
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

### Lesson capabilities

Any lesson can turn on optional features in `config.json` (or with the toggles in Creator Studio):

```json
"capabilities": { "scratchpad": true, "multi_file": true, "telemetry": true, "read_only_files": ["text_utils.py"] }
```

- **`scratchpad`**: a slide-over code runner in any of the five languages, for trying things out. It isn't graded. In the lesson's language, the learner's current lesson files are importable (single-file lessons as `solution.<ext>`).
- **`multi_file`** (code lessons): learners get a file tree and tabs. The starting files live in the lesson's `starter/` folder, nested folders allowed. Your solution versions of the editable files go in `reference/`. Files in `read_only_files` are locked in the editor, and grading always uses the lesson's copy, so editing a helper can't change the result.
- **`telemetry`**: records reading and typing time, attempts, scratchpad runs, and error types (syntax, compile, failed assertion, runtime, timeout) in the local progress database. It never records code. Learners see it under **Insights**, can clear it, and can turn recording off.

See `courses/getting-started/08-modules` for a lesson using all three.

### Article and quiz lessons

For a reading-only lesson, set `"type": "article"` in `config.json`; the lesson is just `lesson.md`, and learners finish it with **Mark Complete**.

For multiple-choice questions, set `"type": "quiz"`. Questions go in `config.json`; answers go in the hidden `solution.json`, with an optional explanation that learners see once they answer correctly:

```json
// config.json
{ "type": "quiz", "title": "Big-O", "questions": [{ "prompt": "Binary search runs in…", "options": ["O(n)", "O(log n)"] }] }
// solution.json
{ "answers": [{ "correct_index": 1, "explanation": "Each step halves the range." }] }
```

A single question can use a shorter form instead: `"options": [...]` in `config.json` with the question in `lesson.md`, and `{"correct_index": 0, "explanation": "…"}` in `solution.json`. Learners submit `{"answers": [1]}` to the lesson's `submit` endpoint. Each question is marked right or wrong, but a wrong answer doesn't reveal the right one. True/false questions are a question with two options.

### System design lessons

Set `"type": "system-design"` in a lesson's `config.json`, with `maxLatencyMs` as the p99 target. Instead of code files, the lesson has `starter.json` (the diagram learners start from) and `solution.json` (a reference design that must pass). Both are React Flow graphs of nodes and edges. **Simulate Traffic** sends 1,000 requests over one second through the learner's diagram by default. An optional `"simulation"` object in `config.json` sets up a richer scenario: `palette` (which node types the canvas offers: `client`, `cdn`, `rateLimiter`, `loadBalancer`, `server`, `cache`, `database`, `replica`, `queue`, `searchIndex`, `lock`, `schemaRegistry`), `traffic` (request count, read/write/static mix, keys, read-your-writes follow-ups, spikes, client app versions, write fan-out cost), graded `faults` (crashes and cut connections), a rolling deploy with a `schema` to evolve, and `goals` (stale reads, failed requests, write latency, queue wait, required node types). `"kind": "fencing"` runs the distributed lock scenario instead. The Studio edits it on the lesson's Simulation tab; `sidecar-go/internal/simulator/scenario.go` documents every field. Grading is by behavior (overloaded servers, p99 latency, unanswered requests), so any design with enough capacity passes. Add `"max_budget": 95` to cap the monthly cost; the engine prices each node (Load Balancer $20, Server $10 plus $10 per connection-pool slot past 4, Database $50 plus $40 for a replica) and fails designs over budget. `GET /simulate/catalog` lists the prices.

Learners can double-click a node to change its settings (a server's connection pool, a database's sync/async replication, a load balancer's algorithm). Every run returns a **timeline** of frames (per-node CPU, pool use, and queue; per-connection traffic) plus events, which the canvas replays with glowing hot spots and a scrubber. The **Chaos** toolkit crashes nodes or cuts connections 30% into the run: load balancers route around failures after health checks notice, and replicated databases fail over. Chaos runs are experiments and don't count as lesson attempts.

See `courses/system-design`. In development the app reads `courses/` live; user courses go in the app data folder (`~/Library/Application Support/dev.freeknowledge.app/courses` on macOS).

## Creator Studio and `.dojo` files

Open **Creator Studio** from the home screen to write courses without touching the file system. Add lessons of any type (code exercise, article, quiz, or system design); each starts from a working example. Quizzes have a question builder, and system design lessons use the same diagram canvas learners do, with a tab each for the starter and solution diagrams. **Check lesson** runs your reference solution (it must pass) and the starter code (it should fail) against your tests. **Export .dojo** checks every lesson and refuses to export until each reference solution passes. Bundled courses are read-only; use **Make an editable copy** to remix one.

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
