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
	"slices"
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
	Ext      string   `json:"ext"`
	Compile  []string `json:"-"`
	Run      []string `json:"-"`
	Requires string   `json:"requires"`
	// TestExt is the hidden tests' extension when they're written in another
	// language (assembly is tested from C); empty means Ext.
	TestExt string `json:"testExt,omitempty"`
}

var languages = []Language{
	{ID: "python", Name: "Python", File: "main.py", Ext: ".py", Run: []string{"python3", "-u", "main.py"}, Requires: "python3"},
	{ID: "javascript", Name: "JavaScript (Node)", File: "main.js", Ext: ".js", Run: []string{"node", "main.js"}, Requires: "node"},
	{ID: "go", Name: "Go", File: "main.go", Ext: ".go", Compile: []string{"go", "build", "-o", "{bin}", "main.go"}, Run: []string{"{bin}"}, Requires: "go"},
	{ID: "c", Name: "C", File: "main.c", Ext: ".c", Compile: []string{"gcc", "-std=c17", "-Wall", "-O0", "-o", "{bin}", "main.c"}, Run: []string{"{bin}"}, Requires: "gcc"},
	{ID: "rust", Name: "Rust", File: "main.rs", Ext: ".rs", Compile: []string{"rustc", "--edition=2021", "-o", "{bin}", "main.rs"}, Run: []string{"{bin}"}, Requires: "rustc"},
	{ID: "assembly", Name: "Assembly (x86-64)", File: "main.s", Ext: ".s", TestExt: ".c", Compile: assemblyCompile(), Run: []string{"{bin}"}, Requires: "gcc"},
}

// TestFile is the name of the lesson's hidden tests in this language.
func (l Language) TestFile() string {
	if l.TestExt != "" {
		return "solution_test" + l.TestExt
	}
	return "solution_test" + l.Ext
}

// rosettaPath exists once Rosetta is installed. Apple Silicon Macs need it
// to run the x86-64 programs assembly lessons build.
var rosettaPath = "/Library/Apple/usr/share/rosetta/rosetta"

// Unavailable reports what must be installed before code in l can run
// (empty if nothing), and a message explaining it.
func (l Language) Unavailable() (missing, message string) {
	if _, err := exec.LookPath(l.Requires); err != nil {
		return l.Requires, l.Requires + " is not installed or not on PATH"
	}
	if l.ID == "assembly" && runtime.GOOS == "darwin" && runtime.GOARCH == "arm64" {
		if _, err := os.Stat(rosettaPath); err != nil {
			return "Rosetta", "Rosetta is not installed, and this Mac needs it to run x86-64 code. Install it by running: softwareupdate --install-rosetta"
		}
	}
	return "", ""
}

// AssemblyFlags are the gcc flags that build x86-64 code on every platform:
// Apple Silicon Macs build for x86_64 and run it under Rosetta.
func AssemblyFlags() []string {
	switch runtime.GOOS {
	case "darwin":
		return []string{"-arch", "x86_64"}
	case "linux":
		return []string{"-Wa,--noexecstack"}
	}
	return nil
}

// assemblyCompile builds a program from main.s. Learners write plain symbol
// names, so on macOS their main is aliased to the _main the linker expects.
func assemblyCompile() []string {
	argv := append([]string{"gcc", "-Wall", "-O0"}, AssemblyFlags()...)
	if runtime.GOOS == "darwin" {
		argv = append(argv, "-Wl,-alias,main,_main")
	}
	return append(argv, "-o", "{bin}", "main.s")
}

// Languages lists every supported language.
func Languages() []Language { return slices.Clone(languages) }

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
	// Missing is what isn't installed: usually Requires, or "Rosetta".
	Missing string `json:"missing,omitempty"`
}

func Runtimes() []RuntimeInfo {
	out := make([]RuntimeInfo, 0, len(languages))
	for _, l := range languages {
		p, _ := exec.LookPath(l.Requires)
		missing, _ := l.Unavailable()
		out = append(out, RuntimeInfo{Language: l, Available: missing == "", Path: p, Missing: missing})
	}
	return out
}

type Request struct {
	Language  string `json:"language"`
	Code      string `json:"code"`
	Stdin     string `json:"stdin,omitempty"`
	TimeoutMs int    `json:"timeoutMs,omitempty"`
	// Files are written beside the program (relative paths) so it can
	// import them; the Scratchpad sends a lesson's files this way.
	Files map[string]string `json:"files,omitempty"`
}

// Limits on Request.Files.
const (
	MaxExtraFiles     = 100
	MaxExtraFileBytes = 5 << 20 // in total
)

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
	if missing, msg := lang.Unavailable(); missing != "" {
		return Result{Phase: PhaseCompile, ExitCode: -1, Error: msg}, nil
	}

	dir, err := os.MkdirTemp("", "fk-run-*")
	if err != nil {
		return Result{}, fmt.Errorf("create workspace: %w", err)
	}
	defer os.RemoveAll(dir)

	if err := writeExtraFiles(dir, lang.File, req.Files); err != nil {
		return Result{Phase: PhaseCompile, ExitCode: -1, Error: err.Error()}, nil
	}
	if err := os.WriteFile(filepath.Join(dir, lang.File), []byte(req.Code), 0o600); err != nil {
		return Result{}, fmt.Errorf("write source: %w", err)
	}

	start := time.Now()
	if len(lang.Compile) > 0 {
		res := Exec(ctx, Command{Dir: dir, Argv: ExpandBin(dir, lang.Compile), Timeout: CompileTimeout, Phase: PhaseCompile}, onOutput)
		if res.ExitCode != 0 || res.TimedOut || ctx.Err() != nil {
			res.DurationMs = time.Since(start).Milliseconds()
			return res, nil
		}
	}

	res := Exec(ctx, Command{Dir: dir, Argv: ExpandBin(dir, lang.Run), Stdin: req.Stdin, Timeout: ClampTimeout(req.TimeoutMs), Phase: PhaseRun}, onOutput)
	res.DurationMs = time.Since(start).Milliseconds()
	return res, nil
}

// writeExtraFiles writes files into dir, skipping the program's own file.
// Paths must be relative and stay inside dir.
func writeExtraFiles(dir, main string, files map[string]string) error {
	if len(files) > MaxExtraFiles {
		return fmt.Errorf("too many files (limit %d)", MaxExtraFiles)
	}
	total := 0
	for p, content := range files {
		total += len(content)
		if total > MaxExtraFileBytes {
			return errors.New("files are too large")
		}
		clean := filepath.Clean(filepath.FromSlash(p))
		if p == "" || filepath.IsAbs(clean) || clean == "." || clean == ".." || strings.HasPrefix(clean, ".."+string(filepath.Separator)) {
			return fmt.Errorf("invalid file path %q", p)
		}
		if clean == main {
			continue
		}
		dst := filepath.Join(dir, clean)
		if err := os.MkdirAll(filepath.Dir(dst), 0o700); err != nil {
			return err
		}
		if err := os.WriteFile(dst, []byte(content), 0o600); err != nil {
			return err
		}
	}
	return nil
}

// ClampTimeout converts a requested timeout to a duration, applying the
// default and the maximum.
func ClampTimeout(ms int) time.Duration {
	if ms <= 0 {
		return DefaultRunTimeout
	}
	return min(time.Duration(ms)*time.Millisecond, MaxRunTimeout)
}

// ExpandBin replaces "{bin}" in args with the platform executable path in dir.
func ExpandBin(dir string, args []string) []string {
	bin := "prog"
	if runtime.GOOS == "windows" {
		bin = "prog.exe"
	}
	out := make([]string, len(args))
	for i, a := range args {
		if a == "{bin}" {
			a = filepath.Join(dir, bin)
		}
		out[i] = a
	}
	return out
}

// Command is one process invocation inside a workspace.
type Command struct {
	Dir     string
	Argv    []string
	Stdin   string
	Env     []string // added to the inherited environment
	Timeout time.Duration
	Phase   Phase
}

// Exec runs c, capturing (and optionally streaming) its output. DurationMs is
// left for the caller to fill in.
func Exec(parent context.Context, c Command, onOutput OutputFunc) Result {
	ctx, cancel := context.WithTimeout(parent, c.Timeout)
	defer cancel()
	phase, argv := c.Phase, c.Argv

	var mu sync.Mutex
	stdout := &capture{stream: "stdout", phase: phase, mu: &mu, onOutput: onOutput}
	stderr := &capture{stream: "stderr", phase: phase, mu: &mu, onOutput: onOutput}

	cmd := exec.CommandContext(ctx, argv[0], argv[1:]...)
	cmd.Dir = c.Dir
	cmd.Stdin = strings.NewReader(c.Stdin)
	if len(c.Env) > 0 {
		cmd.Env = append(os.Environ(), c.Env...)
	}
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
