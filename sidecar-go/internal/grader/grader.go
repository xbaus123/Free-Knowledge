// Package grader runs a lesson's hidden tests against submitted code.
//
// The submission is written as solution.<ext> next to the lesson's
// solution_test.<ext> in a temp workspace, along with a small per-language
// harness. Harnesses append one JSON record per test to $FK_RESULTS, keeping
// test results separate from the program's own stdout. Go and Rust use their
// toolchains' own test output instead.
package grader

import (
	"bufio"
	"context"
	"embed"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/runner"
)

//go:embed harness/*
var harnessFS embed.FS

type Status string

const (
	StatusPass  Status = "pass"
	StatusFail  Status = "fail"
	StatusError Status = "error"
	StatusSkip  Status = "skip"
	statusRun   Status = "run" // started but not finished; only seen in records
)

type TestResult struct {
	Name       string `json:"name"`
	Status     Status `json:"status"`
	Message    string `json:"message,omitempty"`
	DurationMs int64  `json:"durationMs"`
}

type Result struct {
	runner.Result
	Passed bool         `json:"passed"`
	Tests  []TestResult `json:"tests"`
}

var ErrNoReference = errors.New("lesson has no reference solution")

type harness struct {
	files   map[string]string // workspace file → embedded harness file
	inline  map[string]string // workspace file → literal contents
	env     []string
	compile []string
	run     []string
	// parse extracts results from stdout instead of the results file.
	parse func(stdout string) []TestResult
	// display turns raw stdout into what the learner sees.
	display func(stdout string) string
}

var harnesses = map[string]harness{
	"python": {
		files: map[string]string{"fk_harness.py": "harness/fk_harness.py"},
		run:   []string{"python3", "-u", "fk_harness.py"},
	},
	"javascript": {
		files:  map[string]string{"fk_reporter.mjs": "harness/fk_reporter.mjs"},
		inline: map[string]string{"package.json": `{"type":"module"}` + "\n"},
		run:    []string{"node", "--test-reporter=./fk_reporter.mjs", "--test-reporter-destination=stderr", "solution_test.js"},
	},
	"c": {
		files:   map[string]string{"fk_test.h": "harness/fk_test.h"},
		compile: []string{"gcc", "-std=c17", "-Wall", "-O0", "-o", "{bin}", "solution.c", "solution_test.c", "-lm"},
		run:     []string{"{bin}"},
	},
	"go": {
		inline:  map[string]string{"go.mod": "module lesson\n\ngo 1.21\n"},
		env:     []string{"GOTOOLCHAIN=local", "GOFLAGS=-mod=mod", "GOPROXY=off"},
		compile: []string{"go", "test", "-c", "-o", "{bin}", "."},
		run:     []string{"go", "tool", "test2json", "-p", "lesson", "{bin}", "-test.v=test2json"},
		parse:   parseGoTest,
		display: displayGoTest,
	},
	"rust": {
		inline: map[string]string{"fk_lib.rs": "#![allow(dead_code, unused_imports)]\n" +
			"#[path = \"solution.rs\"] mod solution;\n" +
			"pub use solution::*;\n" +
			"#[cfg(test)] #[path = \"solution_test.rs\"] mod solution_test;\n"},
		compile: []string{"rustc", "--edition=2021", "--test", "-o", "{bin}", "fk_lib.rs"},
		run:     []string{"{bin}", "--test-threads=1"},
		parse:   parseRustTest,
	},
}

// Grade runs the lesson's tests against code. Article lessons pass as soon
// as they're submitted (the learner marked them read); quizzes are graded
// with GradeAnswer instead.
func Grade(ctx context.Context, l *course.Lesson, code string, onOutput runner.OutputFunc) (Result, error) {
	if !l.Valid() {
		return Result{}, fmt.Errorf("lesson %s/%s has problems: %s", l.CourseID, l.ID, strings.Join(l.Problems, "; "))
	}
	switch l.Kind {
	case course.KindCode:
	case course.KindArticle:
		return Result{Result: runner.Result{Phase: runner.PhaseRun}, Passed: true, Tests: []TestResult{{Name: "Read the article", Status: StatusPass}}}, nil
	case course.KindQuiz:
		return Result{}, errors.New("quiz lessons are graded by answer, not code")
	default:
		return Result{}, fmt.Errorf("lesson type %q can't be graded here", l.Kind)
	}
	lang, _ := runner.Lookup(l.Language)
	h, ok := harnesses[lang.ID]
	if !ok {
		return Result{}, fmt.Errorf("no test harness for %s", lang.Name)
	}
	start := time.Now()
	finish := func(r Result) (Result, error) {
		r.DurationMs = time.Since(start).Milliseconds()
		return r, nil
	}
	if _, err := exec.LookPath(lang.Requires); err != nil {
		return finish(Result{Result: runner.Result{Phase: runner.PhaseCompile, ExitCode: -1, Error: lang.Requires + " is not installed or not on PATH"}})
	}

	dir, err := os.MkdirTemp("", "fk-grade-*")
	if err != nil {
		return Result{}, fmt.Errorf("create workspace: %w", err)
	}
	defer os.RemoveAll(dir)
	if err := setupWorkspace(dir, l, lang, h, code); err != nil {
		return Result{}, err
	}
	resultsPath := filepath.Join(dir, "fk_results.jsonl")
	env := append([]string{"FK_RESULTS=" + resultsPath}, h.env...)

	if len(h.compile) > 0 {
		res := runner.Exec(ctx, runner.Command{Dir: dir, Argv: runner.ExpandBin(dir, h.compile), Env: env, Timeout: runner.CompileTimeout, Phase: runner.PhaseCompile}, onOutput)
		if res.ExitCode != 0 || res.TimedOut || ctx.Err() != nil {
			return finish(Result{Result: res, Tests: []TestResult{}})
		}
	}

	streamOut, flush := onOutput, func() {}
	if h.display != nil && onOutput != nil {
		streamOut, flush = lineFilter(onOutput, h.display)
	}
	res := runner.Exec(ctx, runner.Command{Dir: dir, Argv: runner.ExpandBin(dir, h.run), Env: env, Timeout: runner.ClampTimeout(l.TimeoutMs), Phase: runner.PhaseRun}, streamOut)
	flush()

	var tests []TestResult
	if h.parse != nil {
		tests = h.parse(res.Stdout)
	} else {
		tests = readResults(resultsPath)
	}
	if h.display != nil {
		res.Stdout = h.display(res.Stdout)
	}
	tests = finalize(tests, res)

	r := Result{Result: res, Tests: tests}
	r.Passed = res.ExitCode == 0 && !res.TimedOut && res.Error == "" && len(tests) > 0
	for _, t := range tests {
		if t.Status != StatusPass && t.Status != StatusSkip {
			r.Passed = false
		}
	}
	return finish(r)
}

// GradeAnswer checks a quiz answer (a zero-based index into the options)
// against the hidden solution.json. A wrong answer doesn't reveal the right
// one, so the learner can try again.
func GradeAnswer(l *course.Lesson, answer int) (Result, error) {
	if !l.Valid() {
		return Result{}, fmt.Errorf("lesson %s/%s has problems: %s", l.CourseID, l.ID, strings.Join(l.Problems, "; "))
	}
	if l.Kind != course.KindQuiz {
		return Result{}, fmt.Errorf("lesson %s/%s isn't a quiz", l.CourseID, l.ID)
	}
	if answer < 0 || answer >= len(l.Options) {
		return Result{}, fmt.Errorf("answer must be between 0 and %d", len(l.Options)-1)
	}
	correct, err := course.ReadQuizAnswer(l.ReferenceFile)
	if err != nil {
		return Result{}, err
	}
	r := Result{Result: runner.Result{Phase: runner.PhaseRun}, Passed: answer == correct}
	t := TestResult{Name: l.Options[answer], Status: StatusPass, Message: "Correct!"}
	if !r.Passed {
		r.ExitCode = 1
		t.Status, t.Message = StatusFail, "Not quite. Try again."
	}
	r.Tests = []TestResult{t}
	return r, nil
}

// Validate grades the lesson's reference solution. Authors use this to prove
// their tests pass before publishing.
func Validate(ctx context.Context, l *course.Lesson, onOutput runner.OutputFunc) (Result, error) {
	if l.ReferenceFile == "" {
		return Result{}, ErrNoReference
	}
	code, err := os.ReadFile(l.ReferenceFile)
	if err != nil {
		return Result{}, err
	}
	return Grade(ctx, l, string(code), onOutput)
}

func setupWorkspace(dir string, l *course.Lesson, lang runner.Language, h harness, code string) error {
	write := func(name string, data []byte) error {
		return os.WriteFile(filepath.Join(dir, name), data, 0o600)
	}
	if err := write("solution"+lang.Ext, []byte(code)); err != nil {
		return err
	}
	tests, err := os.ReadFile(l.TestFile)
	if err != nil {
		return fmt.Errorf("read tests: %w", err)
	}
	if err := write("solution_test"+lang.Ext, tests); err != nil {
		return err
	}
	for name, src := range h.files {
		data, err := harnessFS.ReadFile(src)
		if err != nil {
			return err
		}
		if err := write(name, data); err != nil {
			return err
		}
	}
	for name, data := range h.inline {
		if err := write(name, []byte(data)); err != nil {
			return err
		}
	}
	return nil
}

// readResults reads harness records; a later record for the same test
// replaces an earlier one (e.g. "run" → "pass").
func readResults(path string) []TestResult {
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()
	var out []TestResult
	index := map[string]int{}
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 64*1024), 1<<20)
	for sc.Scan() {
		var t TestResult
		if json.Unmarshal(sc.Bytes(), &t) != nil || t.Name == "" {
			continue
		}
		if i, ok := index[t.Name]; ok {
			out[i] = t
		} else {
			index[t.Name] = len(out)
			out = append(out, t)
		}
	}
	return out
}

// finalize marks tests that started but never reported as errors.
func finalize(tests []TestResult, res runner.Result) []TestResult {
	if tests == nil {
		tests = []TestResult{}
	}
	for i, t := range tests {
		if t.Status != statusRun {
			continue
		}
		tests[i].Status = StatusError
		switch {
		case res.TimedOut:
			tests[i].Message = "timed out"
		default:
			tests[i].Message = fmt.Sprintf("the program crashed during this test (exit code %d)", res.ExitCode)
		}
	}
	return tests
}
