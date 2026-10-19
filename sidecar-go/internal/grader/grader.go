// Package grader runs a lesson's hidden tests against submitted code.
//
// The submission is written as solution.<ext> next to the lesson's
// solution_test.<ext> in a temp workspace, along with a small per-language
// harness. A lesson in several languages has a test file for each; every
// suite runs in its own workspace and the results are merged. Harnesses append one JSON record per test to $FK_RESULTS, keeping
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
	"maps"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
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
	files  map[string]string // workspace file → embedded harness file
	inline map[string]string // workspace file → literal contents
	// generate returns more files given the learner's source files (paths
	// with the language's extension), for harnesses that must list them.
	generate func(sources []string) map[string]string
	env      []string
	// compile may contain "{sources}", expanded to every source file.
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
		compile: []string{"gcc", "-std=c17", "-Wall", "-O0", "-o", "{bin}", "{sources}", "solution_test.c", "-lm"},
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
		generate: rustCrateRoot,
		compile:  []string{"rustc", "--edition=2021", "--test", "-o", "{bin}", "fk_lib.rs"},
		run:      []string{"{bin}", "--test-threads=1"},
		parse:    parseRustTest,
	},
}

// rustCrateRoot declares every source file as a module of one crate, so
// multi-file lessons work without the learner writing `mod` lines. Items in
// solution.rs are re-exported at the root for the tests' `use super::*`.
func rustCrateRoot(sources []string) map[string]string {
	var b strings.Builder
	b.WriteString("#![allow(dead_code, unused_imports)]\n")
	for _, src := range sources {
		if src == "solution.rs" {
			b.WriteString("#[path = \"solution.rs\"] mod solution;\npub use solution::*;\n")
			continue
		}
		fmt.Fprintf(&b, "#[path = %q] pub mod %s;\n", src, rustModName(src))
	}
	b.WriteString("#[cfg(test)] #[path = \"solution_test.rs\"] mod solution_test;\n")
	return map[string]string{"fk_lib.rs": b.String()}
}

// rustModName turns "utils/math.rs" into "utils_math".
func rustModName(path string) string {
	name := []byte(strings.TrimSuffix(path, ".rs"))
	for i, c := range name {
		if !(c == '_' || c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' || c >= '0' && c <= '9') {
			name[i] = '_'
		}
	}
	if len(name) > 0 && name[0] >= '0' && name[0] <= '9' {
		return "m_" + string(name)
	}
	return string(name)
}

// Grade runs the lesson's tests against code (the learner's solution.<ext>). Article lessons pass as soon
// as they're submitted (the learner marked them read); quizzes are graded
// with GradeAnswer instead.
func Grade(ctx context.Context, l *course.Lesson, code string, onOutput runner.OutputFunc) (Result, error) {
	if l.Kind == course.KindCode {
		lang, _ := runner.Lookup(l.Language)
		return GradeFiles(ctx, l, map[string]string{"solution" + lang.Ext: code}, onOutput)
	}
	return GradeFiles(ctx, l, nil, onOutput)
}

// GradeFiles runs the lesson's tests against the learner's files (path →
// content). Single-file lessons expect solution.<ext>; multi-file lessons
// take edits to their starter files, ignoring read-only ones.
func GradeFiles(ctx context.Context, l *course.Lesson, submitted map[string]string, onOutput runner.OutputFunc) (Result, error) {
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
	primary, _ := runner.Lookup(l.Language)
	files, err := workspaceFiles(l, primary, submitted)
	if err != nil {
		return Result{}, err
	}
	if len(l.Tests) == 1 {
		return gradeSuite(ctx, l, l.Tests[0], files, onOutput)
	}
	return gradeSuites(ctx, l, files, onOutput)
}

// gradeSuites runs each language's tests in turn (a lesson in several
// languages) and merges the results, naming each test by its language.
func gradeSuites(ctx context.Context, l *course.Lesson, files map[string]string, onOutput runner.OutputFunc) (Result, error) {
	start := time.Now()
	merged := Result{Result: runner.Result{Phase: runner.PhaseRun}, Passed: true, Tests: []TestResult{}}
	var stdout, stderr, errs []string
	for _, suite := range l.Tests {
		name, _, _ := strings.Cut(suite.Language.Name, " (") // "JavaScript (Node)" → "JavaScript"
		header := fmt.Sprintf("── %s tests ──\n", name)
		if onOutput != nil {
			onOutput(runner.PhaseRun, "stdout", header)
		}
		r, err := gradeSuite(ctx, l, suite, files, onOutput)
		if err != nil {
			return Result{}, err
		}
		stdout = append(stdout, header+r.Stdout)
		if r.Stderr != "" {
			stderr = append(stderr, header+r.Stderr)
		}
		if r.Error != "" {
			errs = append(errs, name+": "+r.Error)
		}
		for _, t := range r.Tests {
			t.Name = name + " · " + t.Name
			merged.Tests = append(merged.Tests, t)
		}
		if !r.Passed {
			merged.Passed = false
			if merged.ExitCode == 0 {
				merged.Phase, merged.ExitCode = r.Phase, r.ExitCode
			}
		}
		merged.TimedOut = merged.TimedOut || r.TimedOut
		merged.Truncated = merged.Truncated || r.Truncated
		if ctx.Err() != nil {
			break
		}
	}
	if !merged.Passed && merged.ExitCode == 0 {
		merged.ExitCode = 1
	}
	merged.Stdout, merged.Stderr, merged.Error = strings.Join(stdout, "\n"), strings.Join(stderr, "\n"), strings.Join(errs, "; ")
	merged.DurationMs = time.Since(start).Milliseconds()
	return merged, nil
}

// gradeSuite runs one language's tests against files in a fresh workspace.
func gradeSuite(ctx context.Context, l *course.Lesson, suite course.TestSuite, files map[string]string, onOutput runner.OutputFunc) (Result, error) {
	lang := suite.Language
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
	sources, err := setupWorkspace(dir, suite, h, files)
	if err != nil {
		return Result{}, err
	}
	resultsPath := filepath.Join(dir, "fk_results.jsonl")
	env := append([]string{"FK_RESULTS=" + resultsPath}, h.env...)

	if len(h.compile) > 0 {
		var argv []string
		for _, a := range runner.ExpandBin(dir, h.compile) {
			if a == "{sources}" {
				for _, src := range sources {
					argv = append(argv, filepath.FromSlash(src))
				}
				continue
			}
			argv = append(argv, a)
		}
		res := runner.Exec(ctx, runner.Command{Dir: dir, Argv: argv, Env: env, Timeout: runner.CompileTimeout, Phase: runner.PhaseCompile}, onOutput)
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

// GradeAnswers checks quiz answers (one zero-based option index per
// question) against the hidden solution.json. Each question gets a result:
// a correct one shows its explanation; a wrong one doesn't reveal the right
// answer, so the learner can try again.
func GradeAnswers(l *course.Lesson, answers []int) (Result, error) {
	if !l.Valid() {
		return Result{}, fmt.Errorf("lesson %s/%s has problems: %s", l.CourseID, l.ID, strings.Join(l.Problems, "; "))
	}
	if l.Kind != course.KindQuiz {
		return Result{}, fmt.Errorf("lesson %s/%s isn't a quiz", l.CourseID, l.ID)
	}
	if len(answers) != len(l.Questions) {
		return Result{}, fmt.Errorf("expected %d answers, got %d", len(l.Questions), len(answers))
	}
	key, err := course.ReadQuizAnswers(l.ReferenceFile)
	if err != nil {
		return Result{}, err
	}
	r := Result{Result: runner.Result{Phase: runner.PhaseRun}, Passed: true, Tests: make([]TestResult, len(answers))}
	for i, a := range answers {
		if a < 0 || a >= len(l.Questions[i].Options) {
			return Result{}, fmt.Errorf("answer to question %d must be between 0 and %d", i+1, len(l.Questions[i].Options)-1)
		}
		t := TestResult{Name: fmt.Sprintf("Question %d", i+1), Status: StatusPass, Message: key[i].Explanation}
		if a != key[i].CorrectIndex {
			t.Status, t.Message = StatusFail, "Not quite. Try again."
			r.Passed = false
		}
		r.Tests[i] = t
	}
	if !r.Passed {
		r.ExitCode = 1
	}
	return r, nil
}

// CheckAnswer checks one quiz answer, for quizzes with immediate feedback.
// Like GradeAnswers, a wrong answer doesn't reveal the right one.
func CheckAnswer(l *course.Lesson, question, answer int) (TestResult, error) {
	if l.Kind != course.KindQuiz || !l.Valid() {
		return TestResult{}, fmt.Errorf("lesson %s/%s isn't a working quiz", l.CourseID, l.ID)
	}
	if !l.ImmediateFeedback {
		return TestResult{}, errors.New("this quiz checks answers when you submit them all")
	}
	if question < 0 || question >= len(l.Questions) {
		return TestResult{}, fmt.Errorf("no question %d", question+1)
	}
	if answer < 0 || answer >= len(l.Questions[question].Options) {
		return TestResult{}, fmt.Errorf("answer to question %d must be between 0 and %d", question+1, len(l.Questions[question].Options)-1)
	}
	key, err := course.ReadQuizAnswers(l.ReferenceFile)
	if err != nil {
		return TestResult{}, err
	}
	t := TestResult{Name: fmt.Sprintf("Question %d", question+1), Status: StatusPass, Message: key[question].Explanation}
	if answer != key[question].CorrectIndex {
		t.Status, t.Message = StatusFail, "Not quite. Try again."
	}
	return t, nil
}

// Validate grades the lesson's reference solution. Authors use this to prove
// their tests pass before publishing.
func Validate(ctx context.Context, l *course.Lesson, onOutput runner.OutputFunc) (Result, error) {
	lang, _ := runner.Lookup(l.Language)
	files := map[string]string{}
	if l.ReferenceFile != "" {
		code, err := os.ReadFile(l.ReferenceFile)
		if err != nil {
			return Result{}, err
		}
		files["solution"+lang.Ext] = string(code)
	}
	if l.Capabilities.MultiFile && l.ReferenceDir != "" {
		ref, err := course.ReadFileTree(l.ReferenceDir)
		if err != nil {
			return Result{}, fmt.Errorf("reference/: %w", err)
		}
		maps.Copy(files, ref)
	}
	if len(files) == 0 {
		return Result{}, ErrNoReference
	}
	return GradeFiles(ctx, l, files, onOutput)
}

// GradeStarter grades the lesson's starting files unchanged. Authors use it
// to confirm the tests don't already pass.
func GradeStarter(ctx context.Context, l *course.Lesson, onOutput runner.OutputFunc) (Result, error) {
	if l.Capabilities.MultiFile {
		return GradeFiles(ctx, l, nil, onOutput)
	}
	return Grade(ctx, l, l.Starter, onOutput)
}

// ErrUnknownFile is returned for submitted files that aren't part of a
// multi-file lesson.
var ErrUnknownFile = errors.New("unknown file")

// workspaceFiles returns the learner's files to grade.
func workspaceFiles(l *course.Lesson, lang runner.Language, submitted map[string]string) (map[string]string, error) {
	if !l.Capabilities.MultiFile {
		code, ok := submitted["solution"+lang.Ext]
		if !ok {
			return nil, fmt.Errorf("the submission is missing solution%s", lang.Ext)
		}
		return map[string]string{"solution" + lang.Ext: code}, nil
	}
	files := make(map[string]string, len(l.Files))
	readOnly := map[string]bool{}
	for _, f := range l.Files {
		files[f.Path] = f.Content
		readOnly[f.Path] = f.ReadOnly
	}
	for path, content := range submitted {
		if _, ok := files[path]; !ok {
			return nil, fmt.Errorf("%w %q", ErrUnknownFile, path)
		}
		if !readOnly[path] { // locked files always come from the lesson
			files[path] = content
		}
	}
	return files, nil
}

// setupWorkspace writes the learner's files, the tests, and the harness into
// dir. It returns the source files (by extension), sorted.
func setupWorkspace(dir string, suite course.TestSuite, h harness, files map[string]string) ([]string, error) {
	lang := suite.Language
	write := func(name string, data []byte) error {
		p := filepath.Join(dir, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(p), 0o700); err != nil {
			return err
		}
		return os.WriteFile(p, data, 0o600)
	}
	var sources []string
	for name, content := range files {
		if !course.ValidFilePath(name) || course.ReservedFilePath(name) {
			return nil, fmt.Errorf("invalid file name %q", name)
		}
		if err := write(name, []byte(content)); err != nil {
			return nil, err
		}
		if strings.HasSuffix(name, lang.Ext) {
			sources = append(sources, name)
		}
	}
	slices.Sort(sources)
	tests, err := os.ReadFile(suite.File)
	if err != nil {
		return nil, fmt.Errorf("read tests: %w", err)
	}
	if err := write("solution_test"+lang.Ext, tests); err != nil {
		return nil, err
	}
	for name, src := range h.files {
		data, err := harnessFS.ReadFile(src)
		if err != nil {
			return nil, err
		}
		if err := write(name, data); err != nil {
			return nil, err
		}
	}
	generated := maps.Clone(h.inline)
	if h.generate != nil {
		generated = h.generate(sources)
	}
	for name, data := range generated {
		if err := write(name, []byte(data)); err != nil {
			return nil, err
		}
	}
	return sources, nil
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
