package course

import (
	"errors"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
)

func write(t *testing.T, path, data string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(data), 0o644); err != nil {
		t.Fatal(err)
	}
}

func lessonIDs(c *Course) []string {
	var ids []string
	for _, l := range c.Lessons {
		ids = append(ids, l.ID)
	}
	return ids
}

func TestLessonOrderAndTitles(t *testing.T) {
	root := t.TempDir()
	write(t, filepath.Join(root, "c1", "course.json"), `{"title":"C1","language":"python"}`)
	write(t, filepath.Join(root, "c1", "02-b", "lesson.md"), "# Second\n")
	write(t, filepath.Join(root, "c1", "02-b", "solution_test.py"), "")
	write(t, filepath.Join(root, "c1", "01-a", "lesson.md"), "intro\n# First\n")
	write(t, filepath.Join(root, "c1", "01-a", "solution_test.py"), "")
	write(t, filepath.Join(root, "c1", "01-a", "starter.py"), "x = 1\n")

	s := NewStore([]Root{{Path: root, Source: "user"}})
	c, err := s.Course("c1")
	if err != nil {
		t.Fatal(err)
	}
	if got := strings.Join(lessonIDs(c), ","); got != "01-a,02-b" {
		t.Fatalf("order: %s", got)
	}
	l, err := s.Lesson("c1", "01-a")
	if err != nil {
		t.Fatal(err)
	}
	if l.Title != "First" || l.Starter != "x = 1\n" || l.Language != "python" || !l.Valid() {
		t.Fatalf("got %+v", l)
	}

	// Explicit order in course.json wins over folder names.
	write(t, filepath.Join(root, "c1", "course.json"), `{"title":"C1","language":"python","lessons":["02-b","01-a"]}`)
	c, _ = s.Course("c1")
	if got := strings.Join(lessonIDs(c), ","); got != "02-b,01-a" {
		t.Fatalf("explicit order: %s", got)
	}
}

func TestProblemsAreReported(t *testing.T) {
	root := t.TempDir()
	write(t, filepath.Join(root, "c", "course.json"), `{"title":"C","lessons":["ok","missing","../escape"]}`)
	write(t, filepath.Join(root, "c", "ok", "config.json"), `{"language":"cobol"}`)

	c, err := NewStore([]Root{{Path: root}}).Course("c")
	if err != nil {
		t.Fatal(err)
	}
	if len(c.Problems) != 2 {
		t.Errorf("course problems: %v", c.Problems)
	}
	if len(c.Lessons) != 1 {
		t.Fatalf("lessons: %+v", c.Lessons)
	}
	p := strings.Join(c.Lessons[0].Problems, "; ")
	if !strings.Contains(p, "lesson.md is missing") || !strings.Contains(p, `unknown language "cobol"`) {
		t.Errorf("lesson problems: %s", p)
	}
}

func TestRejectsTraversal(t *testing.T) {
	root := t.TempDir()
	write(t, filepath.Join(root, "c", "course.json"), `{}`)
	write(t, filepath.Join(root, "c", "l", "lesson.md"), "# L")
	s := NewStore([]Root{{Path: filepath.Join(root, "c")}})
	for _, id := range []string{"..", "../c", "c/l", "", ".hidden"} {
		if _, err := s.Course(id); !errors.Is(err, ErrNotFound) {
			t.Errorf("Course(%q): want ErrNotFound, got %v", id, err)
		}
	}
	s = NewStore([]Root{{Path: root}})
	if _, err := s.Lesson("c", "../c"); !errors.Is(err, ErrNotFound) {
		t.Errorf("Lesson traversal: got %v", err)
	}
}

func TestUserCoursesOverrideBundled(t *testing.T) {
	user, bundled := t.TempDir(), t.TempDir()
	write(t, filepath.Join(bundled, "shared", "course.json"), `{"title":"Bundled"}`)
	write(t, filepath.Join(bundled, "only-bundled", "course.json"), `{"title":"B2"}`)
	write(t, filepath.Join(user, "shared", "course.json"), `{"title":"Mine"}`)
	write(t, filepath.Join(user, "not-a-course", "readme.txt"), "")

	list := NewStore([]Root{{Path: user, Source: "user"}, {Path: bundled, Source: "bundled"}, {Path: filepath.Join(user, "missing")}}).List()
	titles := []string{}
	for _, c := range list {
		titles = append(titles, c.Title+"/"+c.Source)
	}
	slices.Sort(titles)
	if strings.Join(titles, ",") != "B2/bundled,Mine/user" {
		t.Fatalf("got %v", titles)
	}
}

func TestQuizProblems(t *testing.T) {
	root := t.TempDir()
	write(t, filepath.Join(root, "c", "course.json"), `{}`)
	for id, files := range map[string]map[string]string{
		"few-options":  {"config.json": `{"type":"quiz","options":["only"]}`, "solution.json": `{"correct_index":0}`},
		"no-solution":  {"config.json": `{"type":"quiz","options":["a","b"]}`},
		"out-of-range": {"config.json": `{"type":"quiz","options":["a","b"]}`, "solution.json": `{"correct_index":2}`},
		"no-index":     {"config.json": `{"type":"quiz","options":["a","b"]}`, "solution.json": `{}`},
		"ok":           {"config.json": `{"type":"quiz","options":["a","b"]}`, "solution.json": `{"correct_index":1}`},
	} {
		write(t, filepath.Join(root, "c", id, "lesson.md"), "# Q")
		for name, body := range files {
			write(t, filepath.Join(root, "c", id, name), body)
		}
	}
	s := NewStore([]Root{{Path: root}})
	for _, id := range []string{"few-options", "no-solution", "out-of-range", "no-index"} {
		if l, err := s.Lesson("c", id); err != nil || l.Valid() {
			t.Errorf("%s should have problems: %+v %v", id, l, err)
		}
	}
	if l, err := s.Lesson("c", "ok"); err != nil || !l.Valid() || len(l.Options) != 2 {
		t.Errorf("ok: %+v %v", l, err)
	}
}
