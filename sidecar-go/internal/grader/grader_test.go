package grader

import (
	"context"
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

			starter, err := Grade(context.Background(), l, l.Starter, nil)
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
	if err != nil || !l.Valid() || len(l.Options) != 4 {
		t.Fatalf("lesson: %+v %v", l, err)
	}
	if res, err := GradeAnswer(l, 0); err != nil || !res.Passed || res.Tests[0].Name != "Garbage Collection" {
		t.Fatalf("correct answer: %+v %v", res, err)
	}
	res, err := GradeAnswer(l, 2)
	if err != nil || res.Passed || res.Tests[0].Status != StatusFail {
		t.Fatalf("wrong answer: %+v %v", res, err)
	}
	if strings.Contains(res.Tests[0].Message, "Garbage") {
		t.Fatal("a wrong answer must not reveal the right one")
	}
	for _, bad := range []int{-1, 4} {
		if _, err := GradeAnswer(l, bad); err == nil {
			t.Errorf("answer %d should be rejected", bad)
		}
	}
	if _, err := Grade(context.Background(), l, "0", nil); err == nil {
		t.Error("Grade should refuse quizzes")
	}
}
