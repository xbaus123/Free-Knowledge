package runner

import (
	"context"
	"os/exec"
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
