// Package studio creates and edits course packs in the user's course folder.
package studio

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"maps"
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
	// Type is "code", "article", "quiz", or "system-design". It's chosen when
	// the lesson is created and can't change afterwards.
	Type         string `json:"type"`
	Title        string `json:"title"`
	Language     string `json:"language,omitempty"`
	TimeoutMs    int    `json:"timeoutMs,omitempty"`
	MaxLatencyMs int    `json:"maxLatencyMs,omitempty"`
	Markdown     string `json:"markdown"`
	// Code lessons: starter code, hidden tests, and the reference solution.
	// System design lessons: Starter is starter.json and Reference is
	// solution.json (diagram JSON).
	Starter   string `json:"starter"`
	Tests     string `json:"tests"`
	Reference string `json:"reference"`
	// Quiz lessons.
	Questions []QuestionSource `json:"questions,omitempty"`
	// Optional features; see course.Capabilities.
	Capabilities course.Capabilities `json:"capabilities"`
	// Multi-file code lessons: the starting files (path → content) and the
	// reference versions of the editable ones. Starter and Reference are
	// unused for these.
	StarterFiles   map[string]string `json:"starterFiles,omitempty"`
	ReferenceFiles map[string]string `json:"referenceFiles,omitempty"`
}

// QuestionSource is a quiz question with its (hidden) answer.
type QuestionSource struct {
	Prompt       string   `json:"prompt"`
	Options      []string `json:"options"`
	CorrectIndex int      `json:"correctIndex"`
	Explanation  string   `json:"explanation"`
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
	src := LessonSource{ID: l.ID, Type: l.Kind, Title: l.Title, Language: l.Language, TimeoutMs: l.TimeoutMs,
		MaxLatencyMs: l.MaxLatencyMs, Markdown: l.Markdown, Starter: l.Starter, Capabilities: l.Capabilities}
	switch l.Kind {
	case course.KindCode:
		if lang, ok := runner.Lookup(l.Language); ok {
			src.Tests = readOptional(filepath.Join(l.Dir, "solution_test"+lang.Ext))
			src.Reference = readOptional(filepath.Join(l.Dir, "reference"+lang.Ext))
			if l.Capabilities.MultiFile {
				src.StarterFiles = map[string]string{}
				for _, f := range l.Files {
					src.StarterFiles[f.Path] = f.Content
				}
				src.ReferenceFiles = map[string]string{}
				if l.ReferenceDir != "" {
					src.ReferenceFiles, _ = course.ReadFileTree(l.ReferenceDir)
				} else if src.Reference != "" {
					src.ReferenceFiles["solution"+lang.Ext] = src.Reference
				}
			}
		}
	case course.KindSystemDesign:
		src.Reference = readOptional(filepath.Join(l.Dir, "solution.json"))
	case course.KindQuiz:
		answers, _ := course.ReadQuizAnswers(filepath.Join(l.Dir, "solution.json"))
		for i, q := range l.Questions {
			qs := QuestionSource{Prompt: q.Prompt, Options: q.Options}
			if i < len(answers) {
				qs.CorrectIndex, qs.Explanation = answers[i].CorrectIndex, answers[i].Explanation
			}
			src.Questions = append(src.Questions, qs)
		}
	}
	return src, nil
}

func readOptional(path string) string {
	b, _ := os.ReadFile(path)
	return string(b)
}

// CreateLesson adds a lesson of the given type ("" means code) from a
// working example (code: the reference passes and the starter fails; system
// design: likewise for the diagrams) and appends it to the course order.
func (s *Studio) CreateLesson(courseID, title, kind, language string) (string, error) {
	c, err := s.editable(courseID)
	if err != nil {
		return "", err
	}
	if strings.TrimSpace(title) == "" {
		return "", errors.New("title is required")
	}
	if kind == "" {
		kind = course.KindCode
	}
	src := LessonSource{Type: kind, Title: title}
	switch kind {
	case course.KindCode:
		if language == "" {
			language = c.Language
		}
		tpl, ok := templates[language]
		if !ok {
			return "", fmt.Errorf("unsupported language %q", language)
		}
		src.Language, src.Markdown, src.Starter, src.Tests, src.Reference = language, fmt.Sprintf(tpl.markdown, title), tpl.starter, tpl.tests, tpl.reference
	case course.KindArticle:
		src.Markdown = fmt.Sprintf(articleTemplate, title)
	case course.KindQuiz:
		src.Markdown = fmt.Sprintf(quizIntroTemplate, title)
		src.Questions = []QuestionSource{quizTemplate}
	case course.KindSystemDesign:
		src.Markdown = fmt.Sprintf(designMarkdownTemplate, title)
		src.MaxLatencyMs, src.Starter, src.Reference = 200, designStarterTemplate, designSolutionTemplate
	default:
		return "", fmt.Errorf("unknown lesson type %q", kind)
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
	src.ID = id
	if err := s.writeLesson(c.Dir, kind, src, ""); err != nil {
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
	if src.Type != "" && src.Type != l.Kind {
		return fmt.Errorf("a lesson's type can't be changed (this is a %s lesson)", l.Kind)
	}
	if strings.TrimSpace(src.Title) == "" {
		return errors.New("title is required")
	}
	if src.Capabilities.MultiFile && l.Kind != course.KindCode {
		return errors.New("only code lessons can use multiple files")
	}
	switch l.Kind {
	case course.KindCode:
		lang, ok := runner.Lookup(src.Language)
		if !ok {
			return fmt.Errorf("unsupported language %q", src.Language)
		}
		if src.Capabilities.MultiFile {
			// Turning multi-file on: start from the single-file lesson.
			if len(src.StarterFiles) == 0 {
				src.StarterFiles = map[string]string{"solution" + lang.Ext: src.Starter}
				src.ReferenceFiles = map[string]string{"solution" + lang.Ext: src.Reference}
			}
			if err := validateFiles(src.StarterFiles, src.ReferenceFiles, src.Capabilities.ReadOnlyFiles); err != nil {
				return err
			}
		}
		if src.TimeoutMs < 0 || src.TimeoutMs > int(runner.MaxRunTimeout.Milliseconds()) {
			return fmt.Errorf("time limit must be between 0 and %d ms", runner.MaxRunTimeout.Milliseconds())
		}
	case course.KindQuiz:
		if err := validateQuestions(src.Questions); err != nil {
			return err
		}
	case course.KindSystemDesign:
		if src.MaxLatencyMs < 0 || src.MaxLatencyMs > 60_000 {
			return errors.New("latency target must be between 0 and 60000 ms")
		}
		if !json.Valid([]byte(src.Starter)) || !json.Valid([]byte(src.Reference)) {
			return errors.New("starter and solution diagrams must be valid JSON")
		}
	case course.KindArticle:
	default:
		return fmt.Errorf("%s lessons can't be edited in the Studio", l.Kind)
	}
	return s.writeLesson(c.Dir, l.Kind, src, l.Language)
}

// validateFiles checks a multi-file lesson's starter and reference files.
func validateFiles(starter, reference map[string]string, readOnly []string) error {
	if len(starter) == 0 {
		return errors.New("a multi-file lesson needs at least one starter file")
	}
	if len(starter) > course.MaxLessonFiles {
		return fmt.Errorf("a lesson can have at most %d files", course.MaxLessonFiles)
	}
	for path, content := range starter {
		switch {
		case !course.ValidFilePath(path):
			return fmt.Errorf("%q isn't a valid file name (letters, digits, . _ -, and / for folders)", path)
		case course.ReservedFilePath(path):
			return fmt.Errorf("%q is reserved for the grader", path)
		case len(content) > course.MaxLessonFileBytes:
			return fmt.Errorf("%s is larger than 1 MB", path)
		}
	}
	for path := range reference {
		if _, ok := starter[path]; !ok {
			return fmt.Errorf("reference file %q isn't one of the starter files", path)
		}
	}
	for _, path := range readOnly {
		if _, ok := starter[path]; !ok {
			return fmt.Errorf("read-only file %q isn't one of the starter files", path)
		}
	}
	return nil
}

func validateQuestions(qs []QuestionSource) error {
	if len(qs) == 0 {
		return errors.New("a quiz needs at least one question")
	}
	for i, q := range qs {
		if len(q.Options) < 2 {
			return fmt.Errorf("question %d needs at least two options", i+1)
		}
		for _, o := range q.Options {
			if strings.TrimSpace(o) == "" {
				return fmt.Errorf("question %d has an empty option", i+1)
			}
		}
		if q.CorrectIndex < 0 || q.CorrectIndex >= len(q.Options) {
			return fmt.Errorf("question %d needs a correct answer", i+1)
		}
	}
	return nil
}

// lessonConfig is config.json as the Studio writes it.
type lessonConfig struct {
	Type         string                `json:"type,omitempty"`
	Title        string                `json:"title"`
	Language     string                `json:"language,omitempty"`
	TimeoutMs    int                   `json:"timeoutMs,omitempty"`
	MaxLatencyMs int                   `json:"maxLatencyMs,omitempty"`
	Questions    []course.QuizQuestion `json:"questions,omitempty"`
	Capabilities *course.Capabilities  `json:"capabilities,omitempty"`
}

func (s *Studio) writeLesson(courseDir, kind string, src LessonSource, oldLanguage string) error {
	dir := filepath.Join(courseDir, src.ID)
	cfg := lessonConfig{Title: src.Title}
	files := map[string][]byte{"lesson.md": []byte(src.Markdown)}

	caps := src.Capabilities
	if !caps.MultiFile {
		caps.ReadOnlyFiles = nil
	} else {
		caps.ReadOnlyFiles = slices.Sorted(slices.Values(caps.ReadOnlyFiles))
	}
	if caps.Scratchpad || caps.MultiFile || caps.Telemetry {
		cfg.Capabilities = &caps
	}

	switch kind {
	case course.KindCode:
		lang, _ := runner.Lookup(src.Language)
		// Switching language: remove files with the old extension.
		if old, ok := runner.Lookup(oldLanguage); ok && old.Ext != lang.Ext {
			for _, name := range []string{"starter", "solution_test", "reference"} {
				os.Remove(filepath.Join(dir, name+old.Ext))
			}
		}
		cfg.Language, cfg.TimeoutMs = src.Language, src.TimeoutMs
		files["solution_test"+lang.Ext] = []byte(src.Tests)
		if caps.MultiFile {
			// Editable files only: grading always uses the lesson's copy of
			// read-only ones.
			ref := maps.Clone(src.ReferenceFiles)
			for _, p := range caps.ReadOnlyFiles {
				delete(ref, p)
			}
			if err := replaceDir(filepath.Join(dir, "starter"), src.StarterFiles); err != nil {
				return err
			}
			if err := replaceDir(filepath.Join(dir, "reference"), ref); err != nil {
				return err
			}
			os.Remove(filepath.Join(dir, "starter"+lang.Ext))
			os.Remove(filepath.Join(dir, "reference"+lang.Ext))
		} else {
			files["starter"+lang.Ext] = []byte(src.Starter)
			files["reference"+lang.Ext] = []byte(src.Reference)
			os.RemoveAll(filepath.Join(dir, "starter"))
			os.RemoveAll(filepath.Join(dir, "reference"))
		}
	case course.KindArticle:
		cfg.Type = kind
	case course.KindQuiz:
		cfg.Type = kind
		var answers []course.QuizAnswer
		for _, q := range src.Questions {
			cfg.Questions = append(cfg.Questions, course.QuizQuestion{Prompt: strings.TrimSpace(q.Prompt), Options: q.Options})
			answers = append(answers, course.QuizAnswer{CorrectIndex: q.CorrectIndex, Explanation: strings.TrimSpace(q.Explanation)})
		}
		sol, err := json.MarshalIndent(map[string]any{"answers": answers}, "", "  ")
		if err != nil {
			return err
		}
		files["solution.json"] = append(sol, '\n')
	case course.KindSystemDesign:
		cfg.Type, cfg.MaxLatencyMs = kind, src.MaxLatencyMs
		files["starter.json"] = prettyJSON(src.Starter)
		files["solution.json"] = prettyJSON(src.Reference)
	}

	if err := writeJSON(filepath.Join(dir, "config.json"), cfg); err != nil {
		return err
	}
	for name, body := range files {
		if err := writeFile(filepath.Join(dir, name), body); err != nil {
			return err
		}
	}
	return nil
}

// replaceDir makes dir contain exactly files (path → content), building the
// new contents beside it first so a failure leaves the old folder intact.
func replaceDir(dir string, files map[string]string) error {
	tmp := dir + ".tmp-new"
	os.RemoveAll(tmp)
	for path, content := range files {
		p := filepath.Join(tmp, filepath.FromSlash(path))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			os.RemoveAll(tmp)
			return err
		}
		if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
			os.RemoveAll(tmp)
			return err
		}
	}
	if err := os.MkdirAll(tmp, 0o755); err != nil {
		return err
	}
	if err := os.RemoveAll(dir); err != nil {
		os.RemoveAll(tmp)
		return err
	}
	return os.Rename(tmp, dir)
}

// prettyJSON indents diagram JSON so course files diff well in git.
func prettyJSON(s string) []byte {
	var buf bytes.Buffer
	if err := json.Indent(&buf, []byte(s), "", "  "); err != nil {
		return []byte(s)
	}
	buf.WriteByte('\n')
	return buf.Bytes()
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
