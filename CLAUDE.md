# Project Context & Architecture Brief: Offline-First Coding & System Design Learning Platform

## 1. Project Vision

Build a free, open-source, 100% offline-first desktop application that serves as a local alternative to paid platforms like Codecademy. Instead of relying on cloud sandboxes, users download the desktop app and local "course packs" to learn programming languages, low-level systems engineering, and interactive system design directly on their machine with zero internet required.

## 2. Core Technical Stack (Tauri v2 + Go Sidecar + React)

- **Desktop Wrapper:** Tauri v2 (Rust core handling native window management and spawning the sidecar).
- **Frontend UI:** React, TypeScript, Tailwind CSS.
- **Code Editor:** `@monaco-editor/react` (VS Code editing experience offline).
- **System Design Canvas:** `@xyflow/react` (React Flow) for interactive architecture diagrams and traffic simulations.
- **Backend Engine (Sidecar):** Go (Golang) compiled with target-triple naming (`src-tauri/binaries/engine-<target-triple>`) and spawned automatically by Tauri via `@tauri-apps/plugin-shell`.
- **Local Persistence:** SQLite (managed by the Go sidecar) to store user progress, completed lessons, streaks, and saved code/canvas states locally on disk.

## 3. Core Feature Pillars

1. **Local Code Execution & Grading Engine (Go Sidecar):**
   - Receives user code from the React UI via localhost HTTP/WebSockets (`127.0.0.1:14200`).
   - Writes code to isolated temporary workspaces, executes local runtimes/compilers (`python3`, `go test`, `node`, `gcc`, `rustc`) with strict context timeouts (`context.WithTimeout`), captures `stdout`/`stderr`, and returns structured unit test results.
   - Monitors `os.Stdin` for EOF so the Go sidecar self-terminates immediately if the parent Tauri process closes or reloads.
2. **Interactive System Design Sandbox:**
   - Visual mode: Users wire together infrastructure nodes (Load Balancers, API Gateways, Caches, Worker Pools, Databases) in React Flow and run a discrete-event traffic simulator to spot bottlenecks, latency spikes, and single points of failure.
   - Container mode (Docker integration): The Go sidecar communicates with the local Docker Engine socket (`/var/run/docker.sock`) to spin up real multi-container "break & fix" labs and run local load tests against them.
3. **Git-Friendly, Markdown-Driven Curriculum:**
   - Decouple the platform engine from the curriculum so open-source contributors can easily author courses.
   - Each lesson is a self-contained folder on disk containing:
     - `lesson.md` (instructions and concepts)
     - `starter.*` (initial boilerplate code loaded into Monaco)
     - `solution_test.*` (hidden unit test suite executed by the Go runner)
     - `config.json` (metadata, language runtime, time limits, or system design node constraints)
4. **Creator Studio & Custom `.dojo` Export:**
   - A dedicated "Studio Mode" in the React UI for users to visually author their own lessons with split panes for instructions, starter code, and unit tests.
   - Requires creators to successfully validate their tests against a hidden solution locally before exporting.
   - The Go sidecar packages the lesson files into a standard zip archive utilizing a custom `.dojo` extension, allowing users to share single-file courses across community channels that can be imported seamlessly into the app.
5. **Optional Offline AI Tutor (Ollama Integration):**
   - Auto-detects if a local Ollama instance (`http://localhost:11434`) is running.
   - Sends lesson context + user code + compiler/test errors to a local LLM to provide Socratic hints completely offline without paid API keys.

## 4. Initial Implementation Milestones for Claude Code

1. **Step 1 (Scaffold):** Initialize the Tauri v2 + React + TypeScript project, create the `sidecar-go/` module, and configure `package.json` scripts to compile the Go binary into `src-tauri/binaries/engine-<target-triple>`.
2. **Step 2 (Sidecar IPC):** Configure `tauri.conf.json` and `capabilities/default.json` to bundle and spawn the Go sidecar, implement the `os.Stdin` watchdog in Go, and verify `/health` and `/run` communication from React.
3. **Step 3 (Workspace UI):** Build the split-pane learning view: Markdown lesson reader on the left, Monaco code editor on the top-right, and live terminal/test output drawer on the bottom-right.
4. **Step 4 (Course Loader):** Implement the Go file-system parser that reads local lesson folders from disk, serves them to the frontend, and grades user submissions against the hidden test files.
5. **Step 5 (Creator Studio & `.dojo` Export):** Build the authoring UI in React and implement the Go `archive/zip` logic to bundle, export, and import `.dojo` course files locally.
