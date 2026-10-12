// Builds the Go engine to src-tauri/binaries/engine-<target-triple>[.exe],
// the name Tauri's externalBin expects.
//
// Target triple: TAURI_ENV_TARGET_TRIPLE (set by `tauri build --target`), or
// the first CLI argument, or the host triple from rustc.
import { execFileSync } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function hostTriple() {
  const out = execFileSync("rustc", ["-vV"], { encoding: "utf8" });
  const line = out.split("\n").find((l) => l.startsWith("host:"));
  if (!line) throw new Error("could not read host triple from `rustc -vV`");
  return line.slice("host:".length).trim();
}

const triple = process.env.TAURI_ENV_TARGET_TRIPLE || process.argv[2] || hostTriple();

const archMap = {
  x86_64: "amd64",
  aarch64: "arm64",
  i686: "386",
  armv7: "arm",
};
const arch = archMap[triple.split("-")[0]];
const os = triple.includes("apple-darwin")
  ? "darwin"
  : triple.includes("windows")
    ? "windows"
    : triple.includes("linux")
      ? "linux"
      : undefined;
if (!arch || !os) throw new Error(`unsupported target triple: ${triple}`);

const ext = os === "windows" ? ".exe" : "";
const out = join(root, "src-tauri", "binaries", `engine-${triple}${ext}`);
mkdirSync(dirname(out), { recursive: true });

console.log(`[sidecar] building ${os}/${arch} -> ${out}`);
execFileSync("go", ["build", "-trimpath", "-ldflags=-s -w", "-o", out, "."], {
  cwd: join(root, "sidecar-go"),
  stdio: "inherit",
  env: { ...process.env, GOOS: os, GOARCH: arch, CGO_ENABLED: "0" },
});
