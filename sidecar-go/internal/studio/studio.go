// Package studio creates and edits course packs in the user's course folder.
package studio

import (
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/runner"
)

var (
	ErrExists   = errors.New("already exists")
	ErrReadOnly = errors.New("bundled courses can't be edited; make a copy first")
)

// Studio writes to a single root: the user's course folder.
type Studio struct {
	Root    string
	Courses *course.Store
}

type CourseMeta struct {
	Title       string `json:"title"`
	Description string `json:"description"`
	Author      string `json:"author"`
	Version     string `json:"version"`
	Language    string `json:"language,omitempty"`
}

type courseFile struct {
	CourseMeta
	Lessons []string `json:"lessons"`
}

// LessonSource is everything an author edits, including the hidden files.
type LessonSource struct {
	ID string `json:"id"`
	// Type is "code" or "system-design". Read-only: the Studio edits code
	// lessons; system design lessons are edited as files for now.
	Type      string `json:"type,omitempty"`
	Title     string `json:"title"`
	Language  string `json:"language"`
	TimeoutMs int    `json:"timeoutMs,omitempty"`
	Markdown  string `json:"markdown"`
	Starter   string `json:"starter"`
	Tests     string `json:"tests"`
	Reference string `json:"reference"`
}

var slugJunk = regexp.MustCompile(`[^a-z0-9]+`)

// Slug turns a title into a folder-safe ID.
func Slug(title string) string {
	s := strings.Trim(slugJunk.ReplaceAllString(strings.ToLower(title), "-"), "-")
	if len(s) > 48 {
		s = strings.TrimRight(s[:48], "-")
	}
	if s == "" {
		s = "untitled"
	}
	return s
}

// editable returns a user course, refusing bundled ones.
func (s *Studio) editable(id string) (*course.Course, error) {
	c, err := s.Courses.Course(id)
	if err != nil {
		return nil, err
	}
	if c.Source != "user" {
		return nil, ErrReadOnly
	}
	return c, nil
}

func (s *Studio) readCourseFile(c *course.Course) (courseFile, error) {
	var cf courseFile
	raw, err := os.ReadFile(filepath.Join(c.Dir, "course.json"))
	if err != nil {
		return cf, err
	}
	if err := json.Unmarshal(raw, &cf); err != nil {
		return cf, fmt.Errorf("course.json: %w", err)
	}
	// Pin the current order so later edits don't depend on folder names.
	if len(cf.Lessons) == 0 {
		for _, l := range c.Lessons {
			cf.Lessons = append(cf.Lessons, l.ID)
		}
	}
	return cf, nil
}

func writeJSON(path string, v any) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return writeFile(path, append(data, '\n'))
}

// writeFile replaces path atomically so a crash never leaves half a file.
func writeFile(path string, data []byte) error {
	tmp, err := os.CreateTemp(filepath.Dir(path), ".tmp-*")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if _, err := tmp.Write(data); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := os.Chmod(tmp.Name(), 0o644); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}

// uniqueID returns base, or base-2, base-3, ... if taken.
func uniqueID(taken func(string) bool, base string) string {
	id := base
	for n := 2; taken(id); n++ {
		id = fmt.Sprintf("%s-%d", base, n)
	}
	return id
}

func (s *Studio) CreateCourse(meta CourseMeta) (string, error) {
	if strings.TrimSpace(meta.Title) == "" {
		return "", errors.New("title is required")
	}
	if err := os.MkdirAll(s.Root, 0o755); err != nil {
		return "", err
	}
	id := uniqueID(func(id string) bool {
		_, err := s.Courses.Course(id)
		return err == nil
	}, Slug(meta.Title))
	dir := filepath.Join(s.Root, id)
	if err := os.Mkdir(dir, 0o755); err != nil {
		return "", err
	}
	if meta.Version == "" {
		meta.Version = "1.0.0"
	}
	return id, writeJSON(filepath.Join(dir, "course.json"), courseFile{CourseMeta: meta, Lessons: []string{}})
}

func (s *Studio) UpdateCourse(id string, meta CourseMeta, order []string) error {
	c, err := s.editable(id)
	if err != nil {
		return err
	}
	cf, err := s.readCourseFile(c)
	if err != nil {
		return err
	}
	cf.CourseMeta = meta
	if order != nil {
		// A reorder must name exactly the existing lessons.
		a, b := slices.Clone(order), slices.Clone(cf.Lessons)
		slices.Sort(a)
		slices.Sort(b)
		if !slices.Equal(a, b) {
			return errors.New("lesson order must list every lesson exactly once")
		}
		cf.Lessons = order
	}
	return writeJSON(filepath.Join(c.Dir, "course.json"), cf)
}

func (s *Studio) DeleteCourse(id string) error {
	c, err := s.editable(id)
	if err != nil {
		return err
	}
	return os.RemoveAll(c.Dir)
}

// CopyCourse copies any course (typically a bundled one) into the user
// folder under a new ID so it can be edited.
func (s *Studio) CopyCourse(id string) (string, error) {
	c, err := s.Courses.Course(id)
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(s.Root, 0o755); err != nil {
		return "", err
	}
	newID := uniqueID(func(id string) bool {
		_, err := s.Courses.Course(id)
		return err == nil
	}, c.ID+"-copy")
	dst := filepath.Join(s.Root, newID)
	if err := copyDir(c.Dir, dst); err != nil {
		os.RemoveAll(dst)
		return "", err
	}
	// Mark the copy so it's distinguishable from the original.
	copied := &course.Course{ID: newID, Dir: dst, Lessons: c.Lessons}
	cf, err := s.readCourseFile(copied)
	if err != nil {
		return "", err
	}
	cf.Title += " (copy)"
	return newID, writeJSON(filepath.Join(dst, "course.json"), cf)
}

func copyDir(src, dst string) error {
	return filepath.WalkDir(src, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(src, p)
		target := filepath.Join(dst, rel)
		switch {
		case d.IsDir():
			return os.MkdirAll(target, 0o755)
		case d.Type().IsRegular():
			data, err := os.ReadFile(p)
			if err != nil {
				return err
			}
			return os.WriteFile(target, data, 0o644)
		default:
			return nil // skip symlinks and other special files
		}
	})
}

// --- lessons ---

func (s *Studio) Lesson(courseID, lessonID string) (LessonSource, error) {
	l, err := s.Courses.Lesson(courseID, lessonID)
	if err != nil {
		return LessonSource{}, err
	}
	src := LessonSource{ID: l.ID, Type: l.Kind, Title: l.Title, Language: l.Language, TimeoutMs: l.TimeoutMs, Markdown: l.Markdown, Starter: l.Starter}
	if lang, ok := runner.Lookup(l.Language); ok {
		src.Tests = readOptional(filepath.Join(l.Dir, "solution_test"+lang.Ext))
		src.Reference = readOptional(filepath.Join(l.Dir, "reference"+lang.Ext))
	}
	return src, nil
}

func readOptional(path string) string {
	b, _ := os.ReadFile(path)
	return string(b)
}

// CreateLesson adds a lesson with a working example (the reference passes,
// the starter fails) and appends it to the course order.
func (s *Studio) CreateLesson(courseID, title, language string) (string, error) {
	c, err := s.editable(courseID)
	if err != nil {
		return "", err
	}
	if strings.TrimSpace(title) == "" {
		return "", errors.New("title is required")
	}
	if language == "" {
		language = c.Language
	}
	tpl, ok := templates[language]
	if !ok {
		return "", fmt.Errorf("unsupported language %q", language)
	}
	cf, err := s.readCourseFile(c)
	if err != nil {
		return "", err
	}
	id := uniqueID(func(id string) bool {
		_, err := os.Stat(filepath.Join(c.Dir, id))
		return err == nil
	}, fmt.Sprintf("%02d-%s", len(cf.Lessons)+1, Slug(title)))
	if err := os.Mkdir(filepath.Join(c.Dir, id), 0o755); err != nil {
		return "", err
	}
	src := LessonSource{
		ID:        id,
		Title:     title,
		Language:  language,
		Markdown:  fmt.Sprintf(tpl.markdown, title),
		Starter:   tpl.starter,
		Tests:     tpl.tests,
		Reference: tpl.reference,
	}
	if err := s.writeLesson(c.Dir, src, ""); err != nil {
		return "", err
	}
	cf.Lessons = append(cf.Lessons, id)
	return id, writeJSON(filepath.Join(c.Dir, "course.json"), cf)
}

func (s *Studio) SaveLesson(courseID string, src LessonSource) error {
	c, err := s.editable(courseID)
	if err != nil {
		return err
	}
	l, err := s.Courses.Lesson(courseID, src.ID)
	if err != nil {
		return err
	}
	if l.Kind != course.KindCode {
		return errors.New("system design lessons can't be edited in the Studio yet; edit their files directly")
	}
	if _, ok := runner.Lookup(src.Language); !ok {
		return fmt.Errorf("unsupported language %q", src.Language)
	}
	if src.TimeoutMs < 0 || src.TimeoutMs > int(runner.MaxRunTimeout.Milliseconds()) {
		return fmt.Errorf("time limit must be between 0 and %d ms", runner.MaxRunTimeout.Milliseconds())
	}
	return s.writeLesson(c.Dir, src, l.Language)
}

func (s *Studio) writeLesson(courseDir string, src LessonSource, oldLanguage string) error {
	dir := filepath.Join(courseDir, src.ID)
	lang, _ := runner.Lookup(src.Language)
	// Switching language: remove files with the old extension.
	if old, ok := runner.Lookup(oldLanguage); ok && old.Ext != lang.Ext {
		for _, name := range []string{"starter", "solution_test", "reference"} {
			os.Remove(filepath.Join(dir, name+old.Ext))
		}
	}
	type config struct {
		Title     string `json:"title"`
		Language  string `json:"language"`
		TimeoutMs int    `json:"timeoutMs,omitempty"`
	}
	if err := writeJSON(filepath.Join(dir, "config.json"), config{src.Title, src.Language, src.TimeoutMs}); err != nil {
		return err
	}
	files := map[string]string{
		"lesson.md":                src.Markdown,
		"starter" + lang.Ext:       src.Starter,
		"solution_test" + lang.Ext: src.Tests,
		"reference" + lang.Ext:     src.Reference,
	}
	for name, body := range files {
		if err := writeFile(filepath.Join(dir, name), []byte(body)); err != nil {
			return err
		}
	}
	return nil
}

func (s *Studio) DeleteLesson(courseID, lessonID string) error {
	c, err := s.editable(courseID)
	if err != nil {
		return err
	}
	if _, err := s.Courses.Lesson(courseID, lessonID); err != nil {
		return err
	}
	cf, err := s.readCourseFile(c)
	if err != nil {
		return err
	}
	cf.Lessons = slices.DeleteFunc(cf.Lessons, func(id string) bool { return id == lessonID })
	if err := writeJSON(filepath.Join(c.Dir, "course.json"), cf); err != nil {
		return err
	}
	return os.RemoveAll(filepath.Join(c.Dir, lessonID))
}
