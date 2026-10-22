package grader

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/runner"
)

var store = course.NewStore([]course.Root{{Path: filepath.Join("..", "..", "..", "courses"), Source: "bundled"}})

func lesson(t *testing.T, id string) *course.Lesson {
	t.Helper()
	l, err := store.Lesson("getting-started", id)
	if err != nil {
		t.Fatal(err)
	}
	if !l.Valid() {
		t.Fatalf("lesson problems: %v", l.Problems)
	}
	lang, _ := runner.Lookup(l.Language)
	if _, err := exec.LookPath(lang.Requires); err != nil {
		t.Skipf("%s not installed", lang.Requires)
	}
	return l
}

// Every sample lesson: the reference passes and the starter fails.
func TestSampleCourse(t *testing.T) {
	c, err := store.Course("getting-started")
	if err != nil {
		t.Fatal(err)
	}
	if len(c.Problems) > 0 {
		t.Fatalf("course problems: %v", c.Problems)
	}
	for _, s := range c.Lessons {
		if s.Kind != course.KindCode {
			continue // articles and quizzes have their own tests below
		}
		t.Run(s.ID, func(t *testing.T) {
			t.Parallel()
			l := lesson(t, s.ID)

			ref, err := Validate(context.Background(), l, nil)
			if err != nil {
				t.Fatal(err)
			}
			if !ref.Passed {
				t.Fatalf("reference should pass: %+v", ref)
			}

			starter, err := GradeStarter(context.Background(), l, nil)
			if err != nil {
				t.Fatal(err)
			}
			if starter.Passed {
				t.Fatalf("starter should fail: %+v", starter)
			}
			if starter.Phase == runner.PhaseRun {
				var failed int
				for _, tr := range starter.Tests {
					if tr.Status == StatusFail && tr.Message == "" {
						t.Errorf("failed test %q has no message", tr.Name)
					}
					if tr.Status == StatusFail {
						failed++
					}
				}
				if failed == 0 {
					t.Errorf("expected failing tests: %+v", starter.Tests)
				}
			}
		})
	}
}

func TestPythonPrintsStayInStdout(t *testing.T) {
	l := lesson(t, "01-python-greet")
	res, err := Grade(context.Background(), l, "print('debugging')\ndef greet(name):\n    return f'Hello, {name or \"world\"}!'\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	if !res.Passed || strings.TrimSpace(res.Stdout) != "debugging" {
		t.Fatalf("got passed=%v stdout=%q", res.Passed, res.Stdout)
	}
	if res.Tests[0].Name != "greets someone by name" {
		t.Errorf("expected docstring as test name, got %q", res.Tests[0].Name)
	}
}

func TestPythonSyntaxErrorReportsTraceback(t *testing.T) {
	l := lesson(t, "01-python-greet")
	res, err := Grade(context.Background(), l, "def greet(name)\n    return 1\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed || len(res.Tests) != 0 || !strings.Contains(res.Stderr, "SyntaxError") {
		t.Fatalf("got %+v", res)
	}
}

func TestInfiniteLoopTimesOut(t *testing.T) {
	l := lesson(t, "01-python-greet")
	l.TimeoutMs = 500
	res, err := Grade(context.Background(), l, "def greet(name):\n    while True: pass\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed || !res.TimedOut {
		t.Fatalf("got %+v", res)
	}
}

func TestCCrashIsAttributedToTest(t *testing.T) {
	l := lesson(t, "04-c-max")
	res, err := Grade(context.Background(), l, "int max_of(const int *xs, int n) { return *(volatile int *)0; }\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed || len(res.Tests) == 0 || res.Tests[0].Status != StatusError || !strings.Contains(res.Tests[0].Message, "crashed") {
		t.Fatalf("got %+v", res)
	}
}

func TestCCompileError(t *testing.T) {
	l := lesson(t, "04-c-max")
	res, err := Grade(context.Background(), l, "int max_of(const int *xs, int n) { return }\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	if res.Phase != runner.PhaseCompile || res.Passed || res.Stderr == "" {
		t.Fatalf("got %+v", res)
	}
}

func TestGoStreamsReadableOutput(t *testing.T) {
	l := lesson(t, "03-go-reverse")
	code := "package lesson\n\nimport \"fmt\"\n\nfunc Reverse(s string) string {\n\tfmt.Println(\"reversing\", s)\n\treturn s\n}\n"
	var streamed strings.Builder
	res, err := Grade(context.Background(), l, code, func(_ runner.Phase, stream, chunk string) {
		if stream == "stdout" {
			streamed.WriteString(chunk)
		}
	})
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(streamed.String(), `"Action"`) || !strings.Contains(streamed.String(), "reversing hello") {
		t.Fatalf("streamed output not filtered: %q", streamed.String())
	}
	if res.Stdout != streamed.String() {
		t.Errorf("final stdout %q != streamed %q", res.Stdout, streamed.String())
	}
	var names []string
	for _, tr := range res.Tests {
		names = append(names, tr.Name)
	}
	if strings.Join(names, ",") != "TestReverse/ascii,TestReverse/empty,TestReverse/unicode" {
		t.Errorf("want leaf subtests, got %v", names)
	}
}

func TestRustFailureMessage(t *testing.T) {
	l := lesson(t, "05-rust-fizzbuzz")
	res, err := Grade(context.Background(), l, l.Starter, nil)
	if err != nil {
		t.Fatal(err)
	}
	for _, tr := range res.Tests {
		if tr.Name == "fizz" {
			if tr.Status != StatusFail || !strings.Contains(tr.Message, "left") {
				t.Fatalf("got %+v", tr)
			}
			return
		}
	}
	t.Fatalf("no fizz test in %+v", res.Tests)
}

func TestArticlePassesOnSubmit(t *testing.T) {
	l, err := store.Lesson("getting-started", "06-theory-article")
	if err != nil || !l.Valid() || l.Kind != course.KindArticle {
		t.Fatalf("lesson: %+v %v", l, err)
	}
	res, err := Grade(context.Background(), l, "", nil)
	if err != nil || !res.Passed {
		t.Fatalf("got %+v %v", res, err)
	}
}

func TestQuizAnswers(t *testing.T) {
	l, err := store.Lesson("getting-started", "07-knowledge-check")
	if err != nil || !l.Valid() || len(l.Questions) != 1 || len(l.Questions[0].Options) != 4 {
		t.Fatalf("lesson: %+v %v", l, err)
	}
	res, err := GradeAnswers(l, []int{0})
	if err != nil || !res.Passed || res.Tests[0].Name != "Question 1" || !strings.Contains(res.Tests[0].Message, "garbage collector") {
		t.Fatalf("correct answer should pass and explain: %+v %v", res, err)
	}
	res, err = GradeAnswers(l, []int{2})
	if err != nil || res.Passed || res.Tests[0].Status != StatusFail {
		t.Fatalf("wrong answer: %+v %v", res, err)
	}
	if strings.Contains(res.Tests[0].Message, "garbage") {
		t.Fatal("a wrong answer must not reveal the explanation")
	}
	for _, bad := range [][]int{{-1}, {4}, {}, {0, 1}} {
		if _, err := GradeAnswers(l, bad); err == nil {
			t.Errorf("answers %v should be rejected", bad)
		}
	}
	if _, err := Grade(context.Background(), l, "0", nil); err == nil {
		t.Error("Grade should refuse quizzes")
	}
}

func TestCheckAnswerImmediately(t *testing.T) {
	l, err := store.Lesson("system-design", "10-back-of-the-envelope")
	if err != nil || !l.ImmediateFeedback {
		t.Fatalf("lesson: immediate=%v %v", l != nil && l.ImmediateFeedback, err)
	}
	res, err := CheckAnswer(l, 0, 1)
	if err != nil || res.Status != StatusPass || !strings.Contains(res.Message, "86,400") {
		t.Fatalf("correct answer should pass and explain: %+v %v", res, err)
	}
	res, err = CheckAnswer(l, 0, 2)
	if err != nil || res.Status != StatusFail || strings.Contains(res.Message, "86,400") {
		t.Fatalf("a wrong answer fails without revealing the explanation: %+v %v", res, err)
	}
	for _, bad := range [][2]int{{-1, 0}, {99, 0}, {0, -1}, {0, 4}} {
		if _, err := CheckAnswer(l, bad[0], bad[1]); err == nil {
			t.Errorf("%v should be rejected", bad)
		}
	}
	// Quizzes without immediate feedback only grade on submit.
	other, _ := store.Lesson("getting-started", "07-knowledge-check")
	if _, err := CheckAnswer(other, 0, 0); err == nil {
		t.Error("a quiz without immediate feedback should refuse single checks")
	}
}

func testNamed(t *testing.T, res Result, name string) TestResult {
	t.Helper()
	for _, tr := range res.Tests {
		if tr.Name == name {
			return tr
		}
	}
	t.Fatalf("no test %q in %+v", name, res.Tests)
	return TestResult{}
}

func TestPythonFailureDetails(t *testing.T) {
	l := lesson(t, "01-python-greet")
	res, err := Grade(context.Background(), l, "def greet(name):\n    return 'Hi'\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	tr := testNamed(t, res, "greets someone by name")
	want := TestResult{Input: "greet('Ada')", Expected: "'Hello, Ada!'", Actual: "'Hi'"}
	if tr.Status != StatusFail || tr.Input != want.Input || tr.Expected != want.Expected || tr.Actual != want.Actual {
		t.Fatalf("got %+v, want details %+v", tr, want)
	}
	if !strings.Contains(tr.Message, "'Hi' != 'Hello, Ada!'") {
		t.Errorf("the assertion message should be kept: %q", tr.Message)
	}

	// An exception isn't an assertion: no details, just the traceback.
	res, err = Grade(context.Background(), l, "def greet(name):\n    raise ValueError('nope')\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	tr = testNamed(t, res, "greets someone by name")
	if tr.Status != StatusError || tr.Input != "" || tr.Expected != "" || tr.Actual != "" || !strings.Contains(tr.Message, "ValueError: nope") {
		t.Fatalf("got %+v", tr)
	}
}

func TestJavaScriptFailureDetails(t *testing.T) {
	l := lesson(t, "02-javascript-sum")
	res, err := Grade(context.Background(), l, "export function sum(numbers) { return 0; }\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	tr := testNamed(t, res, "sums a few numbers")
	if tr.Status != StatusFail || tr.Input != "sum([1, 2, 3])" || tr.Expected != "6" || tr.Actual != "0" || tr.Message == "" {
		t.Fatalf("got %+v", tr)
	}

	res, err = Grade(context.Background(), l, "export function sum(numbers) { throw new Error('nope'); }\n", nil)
	if err != nil {
		t.Fatal(err)
	}
	tr = testNamed(t, res, "sums a few numbers")
	if tr.Status != StatusFail || tr.Input != "" || tr.Expected != "" || tr.Actual != "" || tr.Message != "nope" {
		t.Fatalf("got %+v", tr)
	}
}

func TestReadResultsDetails(t *testing.T) {
	path := filepath.Join(t.TempDir(), "results.jsonl")
	records := `{"name":"a","status":"fail","message":"5 != 6","durationMs":1,"input":"f(1)","expected":"6","actual":"5"}
{"name":"b","status":"fail","message":"boom","durationMs":2}
`
	if err := os.WriteFile(path, []byte(records), 0o644); err != nil {
		t.Fatal(err)
	}
	got := readResults(path)
	if len(got) != 2 {
		t.Fatalf("got %+v", got)
	}
	if got[0].Input != "f(1)" || got[0].Expected != "6" || got[0].Actual != "5" || got[0].Message != "5 != 6" {
		t.Errorf("details not parsed: %+v", got[0])
	}
	b, _ := json.Marshal(got[1])
	for _, field := range []string{"input", "expected", "actual"} {
		if strings.Contains(string(b), `"`+field+`"`) {
			t.Errorf("missing details should be omitted from %s", b)
		}
	}
}
