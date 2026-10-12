// Package runner compiles and executes user code in throwaway workspaces.
package runner

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

const (
	DefaultRunTimeout = 10 * time.Second
	MaxRunTimeout     = 60 * time.Second
	CompileTimeout    = 60 * time.Second
	// MaxOutputBytes caps captured output per stream so a runaway print loop
	// can't exhaust memory. Output beyond the cap is drained and dropped.
	MaxOutputBytes = 1 << 20
	// killGrace bounds how long we wait for pipes to close after a kill.
	killGrace = 2 * time.Second
)

// Language describes how to build and run a single-file program.
// "{bin}" in a command is replaced with the platform's executable name.
type Language struct {
	ID       string   `json:"id"`
	Name     string   `json:"name"`
	File     string   `json:"file"`
	Compile  []string `json:"-"`
	Run      []string `json:"-"`
	Requires string   `json:"requires"`
}

var languages = []Language{
	{ID: "python", Name: "Python", File: "main.py", Run: []string{"python3", "-u", "main.py"}, Requires: "python3"},
	{ID: "javascript", Name: "JavaScript (Node)", File: "main.js", Run: []string{"node", "main.js"}, Requires: "node"},
	{ID: "go", Name: "Go", File: "main.go", Compile: []string{"go", "build", "-o", "{bin}", "main.go"}, Run: []string{"{bin}"}, Requires: "go"},
	{ID: "c", Name: "C", File: "main.c", Compile: []string{"gcc", "-std=c17", "-Wall", "-O0", "-o", "{bin}", "main.c"}, Run: []string{"{bin}"}, Requires: "gcc"},
	{ID: "rust", Name: "Rust", File: "main.rs", Compile: []string{"rustc", "--edition=2021", "-o", "{bin}", "main.rs"}, Run: []string{"{bin}"}, Requires: "rustc"},
}

func Lookup(id string) (Language, bool) {
	for _, l := range languages {
		if l.ID == id {
			return l, true
		}
	}
	return Language{}, false
}

// RuntimeInfo reports whether a language's toolchain is installed.
type RuntimeInfo struct {
	Language
	Available bool   `json:"available"`
	Path      string `json:"path,omitempty"`
}

func Runtimes() []RuntimeInfo {
	out := make([]RuntimeInfo, 0, len(languages))
	for _, l := range languages {
		p, err := exec.LookPath(l.Requires)
		out = append(out, RuntimeInfo{Language: l, Available: err == nil, Path: p})
	}
	return out
}

type Request struct {
	Language  string `json:"language"`
	Code      string `json:"code"`
	Stdin     string `json:"stdin,omitempty"`
	TimeoutMs int    `json:"timeoutMs,omitempty"`
}

type Phase string

const (
	PhaseCompile Phase = "compile"
	PhaseRun     Phase = "run"
)

type Result struct {
	Phase      Phase  `json:"phase"`
	ExitCode   int    `json:"exitCode"`
	Stdout     string `json:"stdout"`
	Stderr     string `json:"stderr"`
	TimedOut   bool   `json:"timedOut"`
	Truncated  bool   `json:"truncated"`
	DurationMs int64  `json:"durationMs"`
	// Error is set for failures of the engine itself (missing toolchain,
	// workspace errors), as opposed to the user's program failing.
	Error string `json:"error,omitempty"`
}

// OutputFunc receives output chunks as they are produced. It is called from
// multiple goroutines but never concurrently.
type OutputFunc func(phase Phase, stream string, chunk string)

var ErrUnknownLanguage = errors.New("unknown language")

// Run builds (if needed) and executes req in a fresh temp directory, which is
// removed afterwards. Cancelling ctx kills the process tree.
func Run(ctx context.Context, req Request, onOutput OutputFunc) (Result, error) {
	lang, ok := Lookup(req.Language)
	if !ok {
		return Result{}, fmt.Errorf("%w: %q", ErrUnknownLanguage, req.Language)
	}
	if _, err := exec.LookPath(lang.Requires); err != nil {
		return Result{Phase: PhaseCompile, ExitCode: -1, Error: fmt.Sprintf("%s is not installed or not on PATH", lang.Requires)}, nil
	}

	dir, err := os.MkdirTemp("", "fk-run-*")
	if err != nil {
		return Result{}, fmt.Errorf("create workspace: %w", err)
	}
	defer os.RemoveAll(dir)

	if err := os.WriteFile(filepath.Join(dir, lang.File), []byte(req.Code), 0o600); err != nil {
		return Result{}, fmt.Errorf("write source: %w", err)
	}

	bin := "prog"
	if runtime.GOOS == "windows" {
		bin = "prog.exe"
	}
	expand := func(args []string) []string {
		out := make([]string, len(args))
		for i, a := range args {
			if a == "{bin}" {
				a = filepath.Join(dir, bin)
			}
			out[i] = a
		}
		return out
	}

	start := time.Now()
	if len(lang.Compile) > 0 {
		res := execute(ctx, dir, expand(lang.Compile), "", CompileTimeout, PhaseCompile, onOutput)
		if res.ExitCode != 0 || res.TimedOut || ctx.Err() != nil {
			res.DurationMs = time.Since(start).Milliseconds()
			return res, nil
		}
	}

	timeout := DefaultRunTimeout
	if req.TimeoutMs > 0 {
		timeout = min(time.Duration(req.TimeoutMs)*time.Millisecond, MaxRunTimeout)
	}
	res := execute(ctx, dir, expand(lang.Run), req.Stdin, timeout, PhaseRun, onOutput)
	res.DurationMs = time.Since(start).Milliseconds()
	return res, nil
}

func execute(parent context.Context, dir string, argv []string, stdin string, timeout time.Duration, phase Phase, onOutput OutputFunc) Result {
	ctx, cancel := context.WithTimeout(parent, timeout)
	defer cancel()

	var mu sync.Mutex
	stdout := &capture{stream: "stdout", phase: phase, mu: &mu, onOutput: onOutput}
	stderr := &capture{stream: "stderr", phase: phase, mu: &mu, onOutput: onOutput}

	cmd := exec.CommandContext(ctx, argv[0], argv[1:]...)
	cmd.Dir = dir
	cmd.Stdin = strings.NewReader(stdin)
	cmd.Stdout = stdout
	cmd.Stderr = stderr
	cmd.WaitDelay = killGrace
	configureProcessTree(cmd)

	err := cmd.Run()
	res := Result{
		Phase:     phase,
		Stdout:    stdout.buf.String(),
		Stderr:    stderr.buf.String(),
		Truncated: stdout.truncated || stderr.truncated,
		TimedOut:  errors.Is(ctx.Err(), context.DeadlineExceeded),
	}
	switch {
	case cmd.ProcessState != nil:
		res.ExitCode = cmd.ProcessState.ExitCode()
	case err != nil:
		res.ExitCode = -1
		res.Error = err.Error()
	}
	return res
}

// capture buffers up to MaxOutputBytes and forwards chunks to onOutput.
type capture struct {
	stream    string
	phase     Phase
	mu        *sync.Mutex
	onOutput  OutputFunc
	buf       bytes.Buffer
	truncated bool
}

func (c *capture) Write(p []byte) (int, error) {
	c.mu.Lock()
	defer c.mu.Unlock()
	keep := p
	if room := MaxOutputBytes - c.buf.Len(); len(keep) > room {
		keep = keep[:max(room, 0)]
		c.truncated = true
	}
	if len(keep) > 0 {
		c.buf.Write(keep)
		if c.onOutput != nil {
			c.onOutput(c.phase, c.stream, string(keep))
		}
	}
	// Report the full length so the child isn't blocked on a short write.
	return len(p), nil
}
