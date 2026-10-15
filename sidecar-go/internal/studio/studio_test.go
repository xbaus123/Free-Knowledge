package studio

import (
	"archive/zip"
	"bytes"
	"context"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
	"testing"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/runner"
)

func newStudio(t *testing.T) *Studio {
	t.Helper()
	root := t.TempDir()
	store := course.NewStore([]course.Root{
		{Path: root, Source: "user"},
		{Path: filepath.Join("..", "..", "..", "courses"), Source: "bundled"},
	})
	return &Studio{Root: root, Courses: store}
}

// must unwraps (value, error); a panic fails the test with the error.
func must[T any](v T, err error) T {
	if err != nil {
		panic(err)
	}
	return v
}

func TestTemplatesAreValidLessons(t *testing.T) {
	s := newStudio(t)
	id := must(s.CreateCourse(CourseMeta{Title: "Template Check"}))
	for _, lang := range []string{"python", "javascript", "go", "c", "rust"} {
		t.Run(lang, func(t *testing.T) {
			l, _ := runner.Lookup(lang)
			if _, err := exec.LookPath(l.Requires); err != nil {
				t.Skipf("%s not installed", l.Requires)
			}
			lid := must(s.CreateLesson(id, "Hello "+lang, "", lang))
			d := must(s.CheckLesson(context.Background(), id, lid))
			if !d.OK || d.Warning != "" {
				t.Fatalf("template should validate cleanly: %+v ref=%+v starter=%+v", d.LessonCheck, d.Reference, d.Starter)
			}
		})
	}
}

func TestCourseAndLessonEditing(t *testing.T) {
	s := newStudio(t)
	id := must(s.CreateCourse(CourseMeta{Title: "My First Course!"}))
	if id != "my-first-course" {
		t.Fatalf("slug: %q", id)
	}
	if id2 := must(s.CreateCourse(CourseMeta{Title: "My First Course"})); id2 != "my-first-course-2" {
		t.Fatalf("unique id: %q", id2)
	}

	a := must(s.CreateLesson(id, "Variables", "", "python"))
	b := must(s.CreateLesson(id, "Loops", "", "python"))
	if a != "01-variables" || b != "02-loops" {
		t.Fatalf("lesson ids: %s %s", a, b)
	}

	// Switching language replaces the files.
	src := must(s.Lesson(id, a))
	src.Language = "javascript"
	src.Starter, src.Tests, src.Reference = templates["javascript"].starter, templates["javascript"].tests, templates["javascript"].reference
	if err := s.SaveLesson(id, src); err != nil {
		t.Fatal(err)
	}
	dir := filepath.Join(s.Root, id, a)
	if _, err := os.Stat(filepath.Join(dir, "starter.py")); !errors.Is(err, os.ErrNotExist) {
		t.Error("old starter.py should be removed")
	}
	if got := must(s.Lesson(id, a)); got.Language != "javascript" || !strings.Contains(got.Tests, "node:test") {
		t.Fatalf("reloaded: %+v", got)
	}

	// Reordering must list every lesson exactly once.
	if err := s.UpdateCourse(id, CourseMeta{Title: "Renamed"}, []string{b}); err == nil {
		t.Error("partial reorder should fail")
	}
	if err := s.UpdateCourse(id, CourseMeta{Title: "Renamed"}, []string{b, a}); err != nil {
		t.Fatal(err)
	}
	c := must(s.Courses.Course(id))
	if c.Title != "Renamed" || c.Lessons[0].ID != b {
		t.Fatalf("after update: %+v", c)
	}

	if err := s.DeleteLesson(id, b); err != nil {
		t.Fatal(err)
	}
	c = must(s.Courses.Course(id))
	if len(c.Lessons) != 1 || c.Lessons[0].ID != a {
		t.Fatalf("after delete: %+v", c.Lessons)
	}
}

func TestBundledCoursesAreReadOnly(t *testing.T) {
	s := newStudio(t)
	if _, err := s.CreateLesson("getting-started", "x", "", "python"); !errors.Is(err, ErrReadOnly) {
		t.Fatalf("want ErrReadOnly, got %v", err)
	}
	if err := s.DeleteCourse("getting-started"); !errors.Is(err, ErrReadOnly) {
		t.Fatalf("want ErrReadOnly, got %v", err)
	}
	copyID := must(s.CopyCourse("getting-started"))
	c := must(s.Courses.Course(copyID))
	if c.Source != "user" || !strings.HasSuffix(c.Title, "(copy)") || len(c.Lessons) != 8 {
		t.Fatalf("copy: %+v", c)
	}
	if _, err := s.CreateLesson(copyID, "Extra", "", "python"); err != nil {
		t.Fatalf("copy should be editable: %v", err)
	}
}

func TestExportImportRoundTrip(t *testing.T) {
	if _, err := exec.LookPath("python3"); err != nil {
		t.Skip("python3 not installed")
	}
	s := newStudio(t)
	id := must(s.CreateCourse(CourseMeta{Title: "Shareable", Author: "Ada"}))
	lid := must(s.CreateLesson(id, "Answer", "", "python"))
	// A stray file that must not be exported.
	os.WriteFile(filepath.Join(s.Root, id, lid, "notes.txt"), []byte("private"), 0o644)

	dest := filepath.Join(t.TempDir(), "shareable.dojo")
	must(s.Export(context.Background(), id, dest, "test"))

	zr := must(zip.OpenReader(dest))
	var names []string
	for _, f := range zr.File {
		names = append(names, f.Name)
	}
	zr.Close()
	slices.Sort(names)
	want := []string{"01-answer/config.json", "01-answer/lesson.md", "01-answer/reference.py", "01-answer/solution_test.py", "01-answer/starter.py", "course.json", "dojo.json"}
	if !slices.Equal(names, want) {
		t.Fatalf("archive contents:\n got %v\nwant %v", names, want)
	}

	other := newStudio(t)
	res := must(other.Import(dest, false))
	if res.ID != id || res.Title != "Shareable" || res.Lessons != 1 || res.Replaced {
		t.Fatalf("import: %+v", res)
	}
	var conflict *ErrConflict
	if _, err := other.Import(dest, false); !errors.As(err, &conflict) {
		t.Fatalf("second import should conflict, got %v", err)
	}
	if res := must(other.Import(dest, true)); !res.Replaced {
		t.Fatal("replace should report Replaced")
	}
	if d := must(other.CheckLesson(context.Background(), id, lid)); !d.OK {
		t.Fatalf("imported lesson should still validate: %+v", d.LessonCheck)
	}
}

func TestExportRequiresPassingReference(t *testing.T) {
	if _, err := exec.LookPath("python3"); err != nil {
		t.Skip("python3 not installed")
	}
	s := newStudio(t)
	id := must(s.CreateCourse(CourseMeta{Title: "Broken"}))
	lid := must(s.CreateLesson(id, "Bad", "", "python"))
	src := must(s.Lesson(id, lid))
	src.Reference = "def answer():\n    return 41\n"
	if err := s.SaveLesson(id, src); err != nil {
		t.Fatal(err)
	}
	dest := filepath.Join(t.TempDir(), "broken.dojo")
	checks, err := s.Export(context.Background(), id, dest, "test")
	if !errors.Is(err, ErrValidation) || len(checks) != 1 || checks[0].OK || checks[0].Problem == "" {
		t.Fatalf("got %v %+v", err, checks)
	}
	if _, err := os.Stat(dest); !errors.Is(err, os.ErrNotExist) {
		t.Error("no file should be written when validation fails")
	}
}

func zipOf(t *testing.T, files map[string]string) string {
	t.Helper()
	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	for name, body := range files {
		w := must(zw.Create(name))
		w.Write([]byte(body))
	}
	zw.Close()
	p := filepath.Join(t.TempDir(), "x.dojo")
	os.WriteFile(p, buf.Bytes(), 0o644)
	return p
}

func TestImportRejectsMaliciousArchives(t *testing.T) {
	manifest := `{"format":1,"id":"evil"}`
	cases := map[string]map[string]string{
		"zip slip":         {"dojo.json": manifest, "course.json": "{}", "../escape.txt": "x"},
		"absolute path":    {"dojo.json": manifest, "course.json": "{}", "/etc/evil": "x"},
		"nested too deep":  {"dojo.json": manifest, "course.json": "{}", "l/sub/starter.py": "x"},
		"unexpected file":  {"dojo.json": manifest, "course.json": "{}", "l/run.sh": "x"},
		"no manifest":      {"course.json": "{}"},
		"future format":    {"dojo.json": `{"format":99,"id":"evil"}`, "course.json": "{}"},
		"bad id":           {"dojo.json": `{"format":1,"id":"../evil"}`, "course.json": "{}"},
		"backslash":        {"dojo.json": manifest, "course.json": "{}", `l\..\..\x`: "x"},
		"no course.json":   {"dojo.json": manifest},
		"oversized lesson": {"dojo.json": manifest, "course.json": "{}", "l/lesson.md": strings.Repeat("x", maxFileBytes+1)},
	}
	for name, files := range cases {
		t.Run(name, func(t *testing.T) {
			s := newStudio(t)
			if _, err := s.Import(zipOf(t, files), true); err == nil {
				t.Fatal("expected import to fail")
			}
			entries, _ := os.ReadDir(s.Root)
			for _, e := range entries {
				t.Errorf("left behind %q", e.Name())
			}
			if _, err := os.Stat(filepath.Join(filepath.Dir(s.Root), "escape.txt")); err == nil {
				t.Error("file escaped the course folder")
			}
		})
	}
}

func TestBundledDesignLessonValidates(t *testing.T) {
	s := newStudio(t)
	d := must(s.CheckLesson(context.Background(), "system-design", "01-scalability"))
	if !d.OK || d.Warning != "" || d.ReferenceSim == nil || !d.ReferenceSim.Passed || d.StarterSim == nil || d.StarterSim.Passed {
		t.Fatalf("got %+v", d)
	}
}

func TestDesignCourseExports(t *testing.T) {
	s := newStudio(t)
	id := must(s.CopyCourse("system-design"))
	dest := filepath.Join(t.TempDir(), "sd.dojo")
	must(s.Export(context.Background(), id, dest, "test"))
	zr := must(zip.OpenReader(dest))
	defer zr.Close()
	var names []string
	for _, f := range zr.File {
		names = append(names, f.Name)
	}
	if !slices.Contains(names, "01-scalability/starter.json") || !slices.Contains(names, "01-scalability/solution.json") {
		t.Fatalf("archive: %v", names)
	}
}

func TestNonCodeLessonTemplatesValidate(t *testing.T) {
	s := newStudio(t)
	id := must(s.CreateCourse(CourseMeta{Title: "Mixed"}))
	for _, kind := range []string{course.KindArticle, course.KindQuiz, course.KindSystemDesign} {
		t.Run(kind, func(t *testing.T) {
			lid := must(s.CreateLesson(id, "New "+kind, kind, ""))
			d := must(s.CheckLesson(context.Background(), id, lid))
			if !d.OK || d.Warning != "" {
				t.Fatalf("template should validate cleanly: %+v", d.LessonCheck)
			}
			src := must(s.Lesson(id, lid))
			if src.Type != kind || !strings.Contains(src.Markdown, "New "+kind) {
				t.Fatalf("source: %+v", src)
			}
			// Saving the unchanged source works and keeps the lesson valid.
			if err := s.SaveLesson(id, src); err != nil {
				t.Fatal(err)
			}
			if d := must(s.CheckLesson(context.Background(), id, lid)); !d.OK {
				t.Fatalf("after save: %+v", d.LessonCheck)
			}
		})
	}
}

func TestQuizEditing(t *testing.T) {
	s := newStudio(t)
	id := must(s.CreateCourse(CourseMeta{Title: "Quizzes"}))
	lid := must(s.CreateLesson(id, "Check", course.KindQuiz, ""))
	src := must(s.Lesson(id, lid))
	src.Questions = []QuestionSource{
		{Prompt: "2 + 2?", Options: []string{"3", "4"}, CorrectIndex: 1, Explanation: "Basic arithmetic."},
		{Prompt: "Is Go compiled?", Options: []string{"True", "False"}, CorrectIndex: 0},
	}
	if err := s.SaveLesson(id, src); err != nil {
		t.Fatal(err)
	}
	got := must(s.Lesson(id, lid))
	if len(got.Questions) != 2 || got.Questions[0].Explanation != "Basic arithmetic." || got.Questions[1].Prompt != "Is Go compiled?" {
		t.Fatalf("round trip: %+v", got.Questions)
	}
	l := must(s.Courses.Lesson(id, lid))
	if !l.Valid() || len(l.Questions) != 2 {
		t.Fatalf("learner view: %+v", l)
	}

	bad := map[string][]QuestionSource{
		"no questions": nil,
		"one option":   {{Options: []string{"only"}}},
		"empty option": {{Options: []string{"a", " "}}},
		"bad index":    {{Options: []string{"a", "b"}, CorrectIndex: 2}},
	}
	for name, qs := range bad {
		src.Questions = qs
		if err := s.SaveLesson(id, src); err == nil {
			t.Errorf("%s: expected an error", name)
		}
	}

	src = must(s.Lesson(id, lid))
	src.Type = course.KindArticle
	if err := s.SaveLesson(id, src); err == nil {
		t.Error("changing a lesson's type should be refused")
	}
}

func TestMultiFileAuthoringAndExport(t *testing.T) {
	if _, err := exec.LookPath("python3"); err != nil {
		t.Skip("python3 not installed")
	}
	s := newStudio(t)
	id := must(s.CreateCourse(CourseMeta{Title: "Multi"}))
	lid := must(s.CreateLesson(id, "Helpers", "", "python"))

	// Turn on multi-file: the single file becomes solution.py.
	src := must(s.Lesson(id, lid))
	src.Capabilities = course.Capabilities{MultiFile: true, Scratchpad: true, Telemetry: true}
	if err := s.SaveLesson(id, src); err != nil {
		t.Fatal(err)
	}
	src = must(s.Lesson(id, lid))
	if len(src.StarterFiles) != 1 || src.StarterFiles["solution.py"] == "" || src.ReferenceFiles["solution.py"] == "" {
		t.Fatalf("after enabling multi-file: %+v / %+v", src.StarterFiles, src.ReferenceFiles)
	}

	// Add a locked helper the solution uses.
	src.StarterFiles["lib/consts.py"] = "ANSWER = 42\n"
	src.StarterFiles["solution.py"] = "from lib.consts import ANSWER\n\ndef answer():\n    pass\n"
	src.ReferenceFiles["solution.py"] = "from lib.consts import ANSWER\n\ndef answer():\n    return ANSWER\n"
	src.ReferenceFiles["lib/consts.py"] = "ANSWER = 0\n" // dropped: read-only files come from the starter
	src.Capabilities.ReadOnlyFiles = []string{"lib/consts.py"}
	if err := s.SaveLesson(id, src); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(s.Root, id, lid, "reference", "lib", "consts.py")); !errors.Is(err, os.ErrNotExist) {
		t.Error("read-only files shouldn't be saved in reference/")
	}
	d := must(s.CheckLesson(context.Background(), id, lid))
	if !d.OK || d.Warning != "" {
		t.Fatalf("check: %+v ref=%+v", d.LessonCheck, d.Reference)
	}
	l := must(s.Courses.Lesson(id, lid))
	if !l.Capabilities.Scratchpad || !l.Capabilities.Telemetry || len(l.Files) != 2 || !l.Files[0].ReadOnly {
		t.Fatalf("learner view: caps=%+v files=%+v", l.Capabilities, l.Files)
	}

	// Bad edits are refused.
	for name, mutate := range map[string]func(*LessonSource){
		"reserved name":     func(s *LessonSource) { s.StarterFiles["solution_test.py"] = "" },
		"traversal":         func(s *LessonSource) { s.StarterFiles["../x.py"] = "" },
		"unknown read-only": func(s *LessonSource) { s.Capabilities.ReadOnlyFiles = []string{"nope.py"} },
	} {
		bad := must(s.Lesson(id, lid))
		mutate(&bad)
		if err := s.SaveLesson(id, bad); err == nil {
			t.Errorf("%s: expected an error", name)
		}
	}

	quizID := must(s.CreateLesson(id, "Quiz", course.KindQuiz, ""))
	quiz := must(s.Lesson(id, quizID))
	quiz.Capabilities.MultiFile = true
	if err := s.SaveLesson(id, quiz); err == nil {
		t.Error("quizzes can't be multi-file")
	}

	// The archive carries the folders, and the import still validates.
	dest := filepath.Join(t.TempDir(), "multi.dojo")
	must(s.Export(context.Background(), id, dest, "test"))
	other := newStudio(t)
	must(other.Import(dest, false))
	if d := must(other.CheckLesson(context.Background(), id, lid)); !d.OK {
		t.Fatalf("imported lesson: %+v", d.LessonCheck)
	}

	// Turning multi-file off goes back to single files.
	src = must(s.Lesson(id, lid))
	src.Capabilities.MultiFile = false
	if err := s.SaveLesson(id, src); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(s.Root, id, lid, "starter")); !errors.Is(err, os.ErrNotExist) {
		t.Error("starter/ should be removed when multi-file is off")
	}
	if l := must(s.Courses.Lesson(id, lid)); l.Capabilities.ReadOnlyFiles != nil || len(l.Files) != 0 {
		t.Fatalf("single-file again: %+v", l.Capabilities)
	}
}
