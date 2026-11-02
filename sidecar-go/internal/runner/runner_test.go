package runner

import (
	"context"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

func requireTool(t *testing.T, name string) {
	t.Helper()
	if _, err := exec.LookPath(name); err != nil {
		t.Skipf("%s not installed", name)
	}
}

func TestPythonStdoutAndStdin(t *testing.T) {
	requireTool(t, "python3")
	res, err := Run(context.Background(), Request{
		Language: "python",
		Code:     "import sys\nprint('hi', sys.stdin.read().strip())",
		Stdin:    "there",
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.ExitCode != 0 || strings.TrimSpace(res.Stdout) != "hi there" {
		t.Fatalf("unexpected result: %+v", res)
	}
}

func TestTimeoutKillsProcess(t *testing.T) {
	requireTool(t, "python3")
	start := time.Now()
	res, err := Run(context.Background(), Request{
		Language:  "python",
		Code:      "while True: pass",
		TimeoutMs: 300,
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if !res.TimedOut {
		t.Fatalf("expected timeout: %+v", res)
	}
	if time.Since(start) > 3*time.Second {
		t.Fatalf("took too long to kill: %v", time.Since(start))
	}
}

func TestCompileErrorReportsCompilePhase(t *testing.T) {
	requireTool(t, "gcc")
	res, err := Run(context.Background(), Request{Language: "c", Code: "int main( {"}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Phase != PhaseCompile || res.ExitCode == 0 || res.Stderr == "" {
		t.Fatalf("expected compile failure: %+v", res)
	}
}

// Assembly builds for x86-64 everywhere, and main needs no _ prefix on macOS.
func TestAssemblyBuildAndRun(t *testing.T) {
	asm, _ := Lookup("assembly")
	if missing, _ := asm.Unavailable(); missing != "" {
		t.Skipf("%s not installed", missing)
	}
	res, err := Run(context.Background(), Request{
		Language: "assembly",
		Code:     "    .intel_syntax noprefix\n    .text\n    .globl main\nmain:\n    mov eax, 42\n    ret\n",
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Phase != PhaseRun || res.ExitCode != 42 {
		t.Fatalf("unexpected result: %+v", res)
	}
}

// Without Rosetta, an Apple Silicon Mac can't run assembly lessons, and says
// how to install it instead of failing to start the program.
func TestAssemblyNeedsRosetta(t *testing.T) {
	if runtime.GOOS != "darwin" || runtime.GOARCH != "arm64" {
		t.Skip("only Apple Silicon Macs need Rosetta")
	}
	defer func(p string) { rosettaPath = p }(rosettaPath)
	rosettaPath = filepath.Join(t.TempDir(), "missing")
	asm, _ := Lookup("assembly")
	if missing, msg := asm.Unavailable(); missing != "Rosetta" || !strings.Contains(msg, "softwareupdate --install-rosetta") {
		t.Fatalf("got %q, %q", missing, msg)
	}
	res, err := Run(context.Background(), Request{Language: "assembly", Code: "    .globl main\nmain:\n    ret\n"}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.ExitCode != -1 || !strings.Contains(res.Error, "Rosetta") {
		t.Fatalf("unexpected result: %+v", res)
	}
}

func TestGoBuildAndRun(t *testing.T) {
	requireTool(t, "go")
	res, err := Run(context.Background(), Request{
		Language: "go",
		Code:     "package main\nimport \"fmt\"\nfunc main() { fmt.Println(6 * 7) }",
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.ExitCode != 0 || strings.TrimSpace(res.Stdout) != "42" {
		t.Fatalf("unexpected result: %+v", res)
	}
}

func TestOutputIsCapped(t *testing.T) {
	requireTool(t, "python3")
	res, err := Run(context.Background(), Request{
		Language: "python",
		Code:     "import sys\nsys.stdout.write('x' * (3 * 1024 * 1024))",
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if !res.Truncated || len(res.Stdout) != MaxOutputBytes {
		t.Fatalf("expected truncation at %d, got %d (truncated=%v)", MaxOutputBytes, len(res.Stdout), res.Truncated)
	}
}

func TestStreamingCallback(t *testing.T) {
	requireTool(t, "node")
	var got strings.Builder
	_, err := Run(context.Background(), Request{Language: "javascript", Code: "console.log('a'); console.error('b')"},
		func(phase Phase, stream, chunk string) { got.WriteString(stream + ":" + chunk) })
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(got.String(), "stdout:a") || !strings.Contains(got.String(), "stderr:b") {
		t.Fatalf("missing streamed output: %q", got.String())
	}
}

func TestExtraFilesAreImportable(t *testing.T) {
	requireTool(t, "python3")
	res, err := Run(context.Background(), Request{
		Language: "python",
		Code:     "import helper\nfrom pkg import util\nprint(helper.greet(), util.VALUE)",
		Files: map[string]string{
			"helper.py":   "def greet():\n    return 'hello'\n",
			"pkg/util.py": "VALUE = 42\n",
			"main.py":     "raise SystemExit('the program itself must win')",
		},
	}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.ExitCode != 0 || strings.TrimSpace(res.Stdout) != "hello 42" {
		t.Fatalf("unexpected result: %+v", res)
	}
	for _, bad := range []string{"../escape.py", "/etc/passwd", ".."} {
		res, err := Run(context.Background(), Request{Language: "python", Code: "print(1)", Files: map[string]string{bad: "x"}}, nil)
		if err != nil || res.Error == "" {
			t.Errorf("%q should be rejected: %+v %v", bad, res, err)
		}
	}
}
