# FreeKnowledge

A free, open-source, offline-first desktop app for learning programming, systems engineering, and system design. Lessons run entirely on your machine using the compilers and runtimes you already have installed. No cloud sandboxes, accounts, or internet connection required.

> **Status:** early scaffold. The app shell, the Go engine, and code execution work. The lesson workspace, course loader, and system design sandbox are next.

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
- `sidecar-go/`: the engine. `internal/runner` runs code; `internal/server` handles HTTP/WS, auth, and CORS.
- `scripts/build-sidecar.mjs`: compiles the engine to `src-tauri/binaries/engine-<target-triple>`.

### Engine API

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | `{status, version}` |
| GET | `/runtimes` | token | Supported languages and whether each toolchain is installed |
| POST | `/run` | token | `{language, code, stdin?, timeoutMs?}` → `{phase, exitCode, stdout, stderr, timedOut, truncated, durationMs}` |
| GET | `/ws/run?token=…` | token | Send `{"type":"run",…}`; receive `output` messages as they stream, then a `result`. Send `{"type":"cancel"}` to stop. |

Supported languages: Python, JavaScript (Node), Go, C (gcc), Rust (rustc).

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
cd sidecar-go && FK_ENGINE_TOKEN=dev go run . -no-stdin-watchdog
```

## License

[MIT](LICENSE)
