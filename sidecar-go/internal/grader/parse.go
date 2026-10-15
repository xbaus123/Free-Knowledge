package grader

import (
	"encoding/json"
	"regexp"
	"strings"
	"sync"

	"freeknowledge/engine/internal/runner"
)

// --- Go: `go tool test2json` events ---

type goEvent struct {
	Action  string
	Test    string
	Output  string
	Elapsed float64
}

func goEvents(stdout string) []goEvent {
	var out []goEvent
	for line := range strings.Lines(stdout) {
		var ev goEvent
		if json.Unmarshal([]byte(line), &ev) == nil && ev.Action != "" {
			out = append(out, ev)
		}
	}
	return out
}

// isGoFrameworkLine reports lines printed by the testing package rather than
// the program: run/pass markers, summaries, and indented t.Log/t.Error output
// (which is shown in the test result instead).
func isGoFrameworkLine(line string, inTest bool) bool {
	t := strings.TrimSpace(line)
	for _, p := range []string{"=== RUN", "=== PAUSE", "=== CONT", "=== NAME", "--- PASS", "--- FAIL", "--- SKIP"} {
		if strings.HasPrefix(t, p) {
			return true
		}
	}
	if t == "PASS" || t == "FAIL" || strings.HasPrefix(t, "ok ") || strings.HasPrefix(t, "FAIL\t") {
		return true
	}
	return inTest && strings.HasPrefix(line, "    ")
}

func parseGoTest(stdout string) []TestResult {
	var out []TestResult
	index := map[string]int{}
	messages := map[string]*strings.Builder{}
	for _, ev := range goEvents(stdout) {
		if ev.Test == "" {
			continue
		}
		switch ev.Action {
		case "run":
			index[ev.Test] = len(out)
			out = append(out, TestResult{Name: ev.Test, Status: statusRun})
			messages[ev.Test] = &strings.Builder{}
		case "output":
			if b := messages[ev.Test]; b != nil && strings.HasPrefix(ev.Output, "    ") {
				b.WriteString(strings.TrimPrefix(ev.Output, "    "))
			}
		case "pass", "fail", "skip":
			i, ok := index[ev.Test]
			if !ok {
				continue
			}
			out[i].Status = map[string]Status{"pass": StatusPass, "fail": StatusFail, "skip": StatusSkip}[ev.Action]
			out[i].DurationMs = int64(ev.Elapsed * 1000)
			if ev.Action != "pass" {
				out[i].Message = strings.TrimSpace(messages[ev.Test].String())
			}
		}
	}
	// Report leaf tests only: a parent with subtests just aggregates them.
	var leaves []TestResult
	for _, t := range out {
		parent := false
		for _, u := range out {
			if strings.HasPrefix(u.Name, t.Name+"/") {
				parent = true
				break
			}
		}
		if !parent {
			leaves = append(leaves, t)
		}
	}
	return leaves
}

func displayGoTest(stdout string) string {
	var b strings.Builder
	for _, ev := range goEvents(stdout) {
		if ev.Action == "output" && !isGoFrameworkLine(ev.Output, ev.Test != "") {
			b.WriteString(ev.Output)
		}
	}
	return b.String()
}

// --- Rust: libtest's human-readable output ---

var (
	rustResultLine = regexp.MustCompile(`^test (\S+) \.\.\. (ok|FAILED|ignored)`)
	rustFailHeader = regexp.MustCompile(`^---- (\S+) stdout ----$`)
)

func rustName(s string) string { return strings.TrimPrefix(s, "solution_test::") }

func parseRustTest(stdout string) []TestResult {
	var out []TestResult
	index := map[string]int{}
	var current string
	var msg strings.Builder
	flush := func() {
		if i, ok := index[current]; ok && current != "" {
			out[i].Message = strings.TrimSpace(msg.String())
		}
		current = ""
		msg.Reset()
	}
	for line := range strings.Lines(stdout) {
		line = strings.TrimRight(line, "\r\n")
		if m := rustResultLine.FindStringSubmatch(line); m != nil {
			status := map[string]Status{"ok": StatusPass, "FAILED": StatusFail, "ignored": StatusSkip}[m[2]]
			index[rustName(m[1])] = len(out)
			out = append(out, TestResult{Name: rustName(m[1]), Status: status})
			continue
		}
		if m := rustFailHeader.FindStringSubmatch(line); m != nil {
			flush()
			current = rustName(m[1])
			continue
		}
		if current == "" {
			continue
		}
		if line == "failures:" {
			flush()
			continue
		}
		if !strings.HasPrefix(line, "note: run with `RUST_BACKTRACE=1`") {
			msg.WriteString(line + "\n")
		}
	}
	flush()
	return out
}

// --- streaming display filter ---

// lineFilter buffers stdout into whole lines and passes each through display
// before forwarding; stderr is forwarded unchanged. Call flush after the
// process exits to emit any final unterminated line.
func lineFilter(next runner.OutputFunc, display func(string) string) (runner.OutputFunc, func()) {
	var mu sync.Mutex
	var partial strings.Builder
	var lastPhase runner.Phase
	emit := func(phase runner.Phase, s string) {
		if out := display(s); out != "" {
			next(phase, "stdout", out)
		}
	}
	fn := func(phase runner.Phase, stream, chunk string) {
		if stream != "stdout" {
			next(phase, stream, chunk)
			return
		}
		mu.Lock()
		defer mu.Unlock()
		lastPhase = phase
		partial.WriteString(chunk)
		buf := partial.String()
		cut := strings.LastIndexByte(buf, '\n')
		if cut < 0 {
			return
		}
		partial.Reset()
		partial.WriteString(buf[cut+1:])
		emit(phase, buf[:cut+1])
	}
	flush := func() {
		mu.Lock()
		defer mu.Unlock()
		if partial.Len() > 0 {
			emit(lastPhase, partial.String())
			partial.Reset()
		}
	}
	return fn, flush
}
