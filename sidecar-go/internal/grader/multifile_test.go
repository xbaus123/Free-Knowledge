package grader

import (
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/runner"
)

// multiFileLesson writes a multi-file lesson to a temp course and loads it.
func multiFileLesson(t *testing.T, language string, readOnly []string, files map[string]string) *course.Lesson {
	t.Helper()
	root := t.TempDir()
	dir := filepath.Join(root, "c", "l")
	for name, body := range files {
		p := filepath.Join(dir, filepath.FromSlash(name))
		os.MkdirAll(filepath.Dir(p), 0o755)
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	os.WriteFile(filepath.Join(root, "c", "course.json"), []byte(`{}`), 0o644)
	ro := `[]`
	if len(readOnly) > 0 {
		ro = `["` + readOnly[0] + `"]`
	}
	cfg := `{"language":"` + language + `","capabilities":{"multi_file":true,"read_only_files":` + ro + `}}`
	os.WriteFile(filepath.Join(dir, "config.json"), []byte(cfg), 0o644)
	os.WriteFile(filepath.Join(dir, "lesson.md"), []byte("# L"), 0o644)
	l, err := course.NewStore([]course.Root{{Path: root}}).Lesson("c", "l")
	if err != nil {
		t.Fatal(err)
	}
	if !l.Valid() {
		t.Fatalf("problems: %v", l.Problems)
	}
	if _, err := exec.LookPath(map[string]string{"python": "python3", "c": "gcc", "rust": "rustc"}[language]); err != nil {
		t.Skipf("%s toolchain not installed", language)
	}
	return l
}

func TestMultiFilePythonRespectsReadOnly(t *testing.T) {
	l := multiFileLesson(t, "python", []string{"helpers.py"}, map[string]string{
		"starter/helpers.py":     "def double(x):\n    return x * 2\n",
		"starter/solution.py":    "from helpers import double\n\ndef quadruple(x):\n    pass\n",
		"starter/data/notes.txt": "not code\n",
		"reference/solution.py":  "from helpers import double\n\ndef quadruple(x):\n    return double(double(x))\n",
		"solution_test.py":       "import unittest\nfrom solution import quadruple\nfrom helpers import double\n\nclass T(unittest.TestCase):\n    def test_quad(self):\n        self.assertEqual(quadruple(3), 12)\n    def test_helper_intact(self):\n        self.assertEqual(double(5), 10)\n",
	})
	if len(l.Files) != 3 || !l.Files[1].ReadOnly || l.Files[1].Path != "helpers.py" || l.Files[0].Path != "data/notes.txt" {
		t.Fatalf("files: %+v", l.Files)
	}

	ref, err := Validate(context.Background(), l, nil)
	if err != nil || !ref.Passed {
		t.Fatalf("reference should pass: %+v %v", ref, err)
	}
	starter, err := GradeStarter(context.Background(), l, nil)
	if err != nil || starter.Passed {
		t.Fatalf("starter should fail: %+v %v", starter, err)
	}

	// Editing a locked helper has no effect on grading.
	tampered, err := GradeFiles(context.Background(), l, map[string]string{
		"solution.py": "def quadruple(x):\n    return x * 4\n",
		"helpers.py":  "def double(x):\n    return 0\n",
	}, nil)
	if err != nil || !tampered.Passed {
		t.Fatalf("read-only helper must come from the lesson: %+v %v", tampered, err)
	}

	if _, err := GradeFiles(context.Background(), l, map[string]string{"evil.py": "x"}, nil); !errors.Is(err, ErrUnknownFile) {
		t.Fatalf("unknown files should be rejected, got %v", err)
	}
}

func TestMultiFileCCompilesEverySource(t *testing.T) {
	l := multiFileLesson(t, "c", []string{"util.h"}, map[string]string{
		"starter/util.h":       "int twice(int x);\n",
		"starter/util.c":       "int twice(int x) { return x * 2; }\n",
		"starter/solution.c":   "#include \"util.h\"\nint four_times(int x) { return 0; }\n",
		"reference/solution.c": "#include \"util.h\"\nint four_times(int x) { return twice(twice(x)); }\n",
		"solution_test.c":      "#include \"fk_test.h\"\nint four_times(int x);\nTEST(four) { EXPECT_EQ_INT(four_times(3), 12); }\n",
	})
	if res, err := Validate(context.Background(), l, nil); err != nil || !res.Passed {
		t.Fatalf("reference: %+v %v", res, err)
	}
}

func TestMultiFileRustModules(t *testing.T) {
	l := multiFileLesson(t, "rust", nil, map[string]string{
		"starter/geometry/area.rs": "pub fn square(side: u32) -> u32 { side * side }\n",
		"starter/solution.rs":      "pub fn total(sides: &[u32]) -> u32 { 0 }\n",
		"reference/solution.rs":    "use crate::geometry_area::square;\npub fn total(sides: &[u32]) -> u32 { sides.iter().map(|s| square(*s)).sum() }\n",
		"solution_test.rs":         "use super::*;\n#[test]\nfn sums() { assert_eq!(total(&[2, 3]), 13); }\n",
	})
	if res, err := Validate(context.Background(), l, nil); err != nil || !res.Passed {
		t.Fatalf("reference: %+v %v", res, err)
	}
	if rustModName("9lives/my-mod.rs") != "m_9lives_my_mod" {
		t.Errorf("rustModName: %q", rustModName("9lives/my-mod.rs"))
	}
}

func TestMultiFileProblems(t *testing.T) {
	root := t.TempDir()
	dir := filepath.Join(root, "c", "l")
	os.MkdirAll(filepath.Join(dir, "starter"), 0o755)
	os.WriteFile(filepath.Join(root, "c", "course.json"), []byte(`{}`), 0o644)
	os.WriteFile(filepath.Join(dir, "lesson.md"), []byte("# L"), 0o644)
	os.WriteFile(filepath.Join(dir, "solution_test.py"), []byte(""), 0o644)
	os.WriteFile(filepath.Join(dir, "starter", "fk_harness.py"), []byte(""), 0o644)
	os.WriteFile(filepath.Join(dir, "config.json"), []byte(`{"language":"python","capabilities":{"multi_file":true,"read_only_files":["missing.py"]}}`), 0o644)
	l, err := course.NewStore([]course.Root{{Path: root}}).Lesson("c", "l")
	if err != nil {
		t.Fatal(err)
	}
	if len(l.Problems) != 2 {
		t.Fatalf("want reserved-name and missing read-only problems, got %v", l.Problems)
	}
}

// A full-stack lesson: a Python backend and a JavaScript frontend, each with
// its own tests, in one workspace.
func TestMultiLanguageLesson(t *testing.T) {
	for _, tool := range []string{"python3", "node"} {
		if _, err := exec.LookPath(tool); err != nil {
			t.Skipf("%s not installed", tool)
		}
	}
	root := t.TempDir()
	files := map[string]string{
		"course.json":             `{}`,
		"l/lesson.md":             "# Full stack",
		"l/config.json":           `{"languages":["python","javascript"],"capabilities":{"multi_file":true}}`,
		"l/starter/solution.py":   "def price_with_tax(cents):\n    pass\n",
		"l/starter/solution.js":   "export function formatPrice(cents) {}\n",
		"l/reference/solution.py": "def price_with_tax(cents):\n    return round(cents * 1.2)\n",
		"l/reference/solution.js": "export function formatPrice(cents) {\n  return `$${(cents / 100).toFixed(2)}`;\n}\n",
		"l/solution_test.py":      "import unittest\nfrom solution import price_with_tax\n\nclass T(unittest.TestCase):\n    def test_tax(self):\n        \"\"\"adds 20% tax\"\"\"\n        self.assertEqual(price_with_tax(1000), 1200)\n",
		"l/solution_test.js":      "import { test } from \"node:test\";\nimport assert from \"node:assert/strict\";\nimport { formatPrice } from \"./solution.js\";\n\ntest(\"formats cents as dollars\", () => {\n  assert.equal(formatPrice(1200), \"$12.00\");\n});\n",
	}
	for name, body := range files {
		p := filepath.Join(root, "c", filepath.FromSlash(name))
		os.MkdirAll(filepath.Dir(p), 0o755)
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	l, err := course.NewStore([]course.Root{{Path: root}}).Lesson("c", "l")
	if err != nil || !l.Valid() {
		t.Fatalf("lesson: %v %v", err, l.Problems)
	}
	if l.Language != "python" || len(l.Languages) != 2 || len(l.Tests) != 2 || len(l.Files) != 2 {
		t.Fatalf("languages %v, %d suites, files %+v", l.Languages, len(l.Tests), l.Files)
	}

	var streamed string
	ref, err := Validate(context.Background(), l, func(_ runner.Phase, _ string, chunk string) { streamed += chunk })
	if err != nil || !ref.Passed || len(ref.Tests) != 2 {
		t.Fatalf("reference: %+v %v", ref, err)
	}
	if ref.Tests[0].Name != "Python · adds 20% tax" || ref.Tests[1].Name != "JavaScript · formats cents as dollars" {
		t.Errorf("test names: %+v", ref.Tests)
	}
	if !strings.Contains(streamed, "── Python tests ──") || !strings.Contains(streamed, "── JavaScript tests ──") {
		t.Errorf("output should label each language's tests: %q", streamed)
	}

	// The backend done but the frontend not: one suite fails, so the lesson does.
	half, err := GradeFiles(context.Background(), l, map[string]string{"solution.py": files["l/reference/solution.py"]}, nil)
	if err != nil || half.Passed || half.Tests[0].Status != StatusPass || half.Tests[1].Status == StatusPass {
		t.Fatalf("half done: %+v %v", half, err)
	}
}

func TestMultiLanguageLessonProblems(t *testing.T) {
	root := t.TempDir()
	write := func(name, body string) {
		p := filepath.Join(root, "c", filepath.FromSlash(name))
		os.MkdirAll(filepath.Dir(p), 0o755)
		os.WriteFile(p, []byte(body), 0o644)
	}
	write("course.json", `{}`)
	for id, cfg := range map[string]string{
		"single-file": `{"languages":["python","javascript"]}`,
		"unknown":     `{"languages":["python","cobol"],"capabilities":{"multi_file":true}}`,
		"twice":       `{"languages":["python","python"],"capabilities":{"multi_file":true}}`,
		"mismatch":    `{"language":"javascript","languages":["python","javascript"],"capabilities":{"multi_file":true}}`,
		"no-js-tests": `{"languages":["python","javascript"],"capabilities":{"multi_file":true}}`,
	} {
		write(id+"/config.json", cfg)
		write(id+"/lesson.md", "# L")
		write(id+"/starter/solution.py", "")
		write(id+"/solution_test.py", "")
		if id != "no-js-tests" {
			write(id+"/solution_test.js", "")
		}
	}
	store := course.NewStore([]course.Root{{Path: root}})
	for _, id := range []string{"single-file", "unknown", "twice", "mismatch", "no-js-tests"} {
		l, err := store.Lesson("c", id)
		if err != nil || l.Valid() {
			t.Errorf("%s should have problems: %v %v", id, err, l)
		}
	}
}
