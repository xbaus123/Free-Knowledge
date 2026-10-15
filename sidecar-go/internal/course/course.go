// Package course reads course packs from disk.
//
// Layout:
//
//	<root>/<course-id>/course.json
//	<root>/<course-id>/<lesson-id>/lesson.md
//	<root>/<course-id>/<lesson-id>/config.json        (optional)
//	<root>/<course-id>/<lesson-id>/starter.<ext>      (optional; loaded into the editor)
//	<root>/<course-id>/<lesson-id>/solution_test.<ext>
//	<root>/<course-id>/<lesson-id>/reference.<ext>    (optional; author's solution, used for validation)
//
// System design lessons ("type": "system-design" in config.json) use
// starter.json (the initial diagram) and solution.json (a reference design
// that must pass the simulator) instead of code and tests.
//
// Article lessons ("type": "article") are just lesson.md. Quiz lessons
// ("type": "quiz") list their questions in config.json and the answers in
// solution.json, which stays hidden:
//
//	config.json:   {"type": "quiz", "questions": [{"prompt": "…", "options": ["…", "…"]}]}
//	solution.json: {"answers": [{"correct_index": 0, "explanation": "…"}]}
//
// Any lesson may enable optional capabilities in config.json:
//
//	"capabilities": {"scratchpad": true, "multi_file": true, "telemetry": true,
//	                 "read_only_files": ["helpers.py"]}
//
// A multi-file code lesson keeps its starting files in starter/ (any number,
// in subfolders if needed) and may overlay them with reference/ for
// validation. Files in read_only_files are shown locked, and grading always
// uses the lesson's copy of them.
//
// A single question may instead use top-level "options" with the question
// in lesson.md, and solution.json {"correct_index": 0, "explanation": "…"}.
//
// Folder names are the IDs. Lessons are ordered by course.json "lessons" if
// present, otherwise by folder name (use 01-, 02- prefixes).
//
// Packs are re-read on every call so authors see edits immediately.
package course

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"

	"freeknowledge/engine/internal/runner"
)

var (
	ErrNotFound = errors.New("not found")
	idPattern   = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`)
)

// ValidID reports whether s is safe to use as a course or lesson folder name.
func ValidID(s string) bool { return idPattern.MatchString(s) && !strings.Contains(s, "..") }

// Root is a directory containing course folders.
type Root struct {
	Path   string
	Source string // "user" or "bundled"
}

type Store struct {
	roots []Root
}

// NewStore searches roots in order; an earlier root wins when two contain
// the same course ID, so user courses can override bundled ones.
func NewStore(roots []Root) *Store { return &Store{roots: roots} }

type courseFile struct {
	Title       string   `json:"title"`
	Description string   `json:"description"`
	Author      string   `json:"author"`
	Version     string   `json:"version"`
	Language    string   `json:"language"`
	Lessons     []string `json:"lessons"`
}

type lessonConfig struct {
	Title        string         `json:"title"`
	Language     string         `json:"language"`
	Type         string         `json:"type"` // "code" (default) or "system-design"
	TimeoutMs    int            `json:"timeoutMs"`
	MaxLatencyMs int            `json:"maxLatencyMs"` // system design: p99 latency target
	MaxBudget    int            `json:"max_budget"`   // system design: monthly cost limit in dollars
	Questions    []QuizQuestion `json:"questions"`    // quiz
	Options      []string       `json:"options"`      // quiz with one question (short form)
	Capabilities Capabilities   `json:"capabilities"`
}

// Capabilities are optional per-lesson features.
type Capabilities struct {
	// Scratchpad offers a free-form code runner beside the lesson.
	Scratchpad bool `json:"scratchpad"`
	// MultiFile gives code lessons a file tree instead of a single file.
	MultiFile bool `json:"multi_file"`
	// Telemetry records local learning metrics (time, attempts, error kinds).
	Telemetry bool `json:"telemetry"`
	// ReadOnlyFiles are starter files learners can see but not edit.
	ReadOnlyFiles []string `json:"read_only_files,omitempty"`
}

// LessonFile is one file of a multi-file lesson's starting workspace.
type LessonFile struct {
	Path     string `json:"path"`
	Content  string `json:"content"`
	ReadOnly bool   `json:"readOnly,omitempty"`
}

// Limits for multi-file lessons.
const (
	MaxLessonFiles     = 100
	MaxLessonFileBytes = 1 << 20
	maxPathDepth       = 4
)

var pathSegment = regexp.MustCompile(`^[A-Za-z0-9_][A-Za-z0-9._-]{0,63}$`)

// ValidFilePath reports whether p is a safe relative path for a lesson file:
// slash-separated, no "..", at most a few folders deep.
func ValidFilePath(p string) bool {
	parts := strings.Split(p, "/")
	if len(parts) > maxPathDepth || len(p) > 200 {
		return false
	}
	for _, seg := range parts {
		if !pathSegment.MatchString(seg) || strings.Contains(seg, "..") {
			return false
		}
	}
	return true
}

// ReservedFilePath reports names the grader writes itself (tests and
// harness files), which lesson files must not use.
func ReservedFilePath(p string) bool {
	base := filepath.Base(p)
	return p == "go.mod" || p == "package.json" || strings.HasPrefix(base, "solution_test.") || strings.HasPrefix(base, "fk_")
}

// ReadFileTree reads every regular file under root as a path→content map.
func ReadFileTree(root string) (map[string]string, error) {
	files := map[string]string{}
	err := filepath.WalkDir(root, func(p string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || !d.Type().IsRegular() {
			return nil
		}
		rel, _ := filepath.Rel(root, p)
		rel = filepath.ToSlash(rel)
		if !ValidFilePath(rel) {
			return fmt.Errorf("invalid file name %q", rel)
		}
		if len(files) >= MaxLessonFiles {
			return fmt.Errorf("more than %d files", MaxLessonFiles)
		}
		info, err := d.Info()
		if err != nil {
			return err
		}
		if info.Size() > MaxLessonFileBytes {
			return fmt.Errorf("%s is larger than 1 MB", rel)
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return err
		}
		files[rel] = string(b)
		return nil
	})
	return files, err
}

// QuizQuestion is the public part of a quiz question; answers live in
// solution.json.
type QuizQuestion struct {
	Prompt  string   `json:"prompt,omitempty"` // empty: the question is in lesson.md
	Options []string `json:"options"`
}

// QuizAnswer is the hidden part of a quiz question.
type QuizAnswer struct {
	CorrectIndex int    `json:"correct_index"`
	Explanation  string `json:"explanation,omitempty"` // shown after a correct answer
}

// Lesson kinds.
const (
	KindCode         = "code"
	KindSystemDesign = "system-design"
	KindArticle      = "article"
	KindQuiz         = "quiz"
)

type Course struct {
	ID          string          `json:"id"`
	Title       string          `json:"title"`
	Description string          `json:"description"`
	Author      string          `json:"author,omitempty"`
	Version     string          `json:"version,omitempty"`
	Language    string          `json:"language,omitempty"`
	Source      string          `json:"source"`
	Lessons     []LessonSummary `json:"lessons"`
	Problems    []string        `json:"problems,omitempty"`
	Dir         string          `json:"-"`
}

type LessonSummary struct {
	ID       string   `json:"id"`
	Title    string   `json:"title"`
	Language string   `json:"language"`
	Kind     string   `json:"kind"`
	Problems []string `json:"problems,omitempty"`
}

// Lesson is everything the UI needs to show a lesson. Test and reference
// files are paths only and are never sent to the frontend.
type Lesson struct {
	LessonSummary
	CourseID     string         `json:"courseId"`
	Markdown     string         `json:"markdown"`
	Starter      string         `json:"starter"` // code, or diagram JSON for system design
	TimeoutMs    int            `json:"timeoutMs"`
	MaxLatencyMs int            `json:"maxLatencyMs,omitempty"`
	MaxBudget    int            `json:"maxBudget,omitempty"`
	Questions    []QuizQuestion `json:"questions,omitempty"`
	Capabilities Capabilities   `json:"capabilities"`
	// Files is the starting workspace of a multi-file code lesson.
	Files []LessonFile `json:"files,omitempty"`
	Dir   string       `json:"-"`
	// ReferenceDir overlays Files for validation (multi-file lessons).
	ReferenceDir  string `json:"-"`
	TestFile      string `json:"-"`
	ReferenceFile string `json:"-"`
}

// Valid reports whether the lesson can be graded.
func (l *Lesson) Valid() bool { return len(l.Problems) == 0 }

// List returns every course across all roots, without lesson bodies.
func (s *Store) List() []Course {
	var out []Course
	seen := map[string]bool{}
	for _, root := range s.roots {
		entries, err := os.ReadDir(root.Path)
		if err != nil {
			continue // a missing user dir is normal on first launch
		}
		for _, e := range entries {
			if !e.IsDir() || !ValidID(e.Name()) || seen[e.Name()] {
				continue
			}
			c, err := loadCourse(root, e.Name())
			if errors.Is(err, ErrNotFound) {
				continue // not a course folder
			}
			seen[e.Name()] = true
			out = append(out, *c)
		}
	}
	return out
}

func (s *Store) Course(id string) (*Course, error) {
	if !ValidID(id) {
		return nil, ErrNotFound
	}
	for _, root := range s.roots {
		c, err := loadCourse(root, id)
		if err == nil {
			return c, nil
		}
		if !errors.Is(err, ErrNotFound) {
			return nil, err
		}
	}
	return nil, ErrNotFound
}

func (s *Store) Lesson(courseID, lessonID string) (*Lesson, error) {
	c, err := s.Course(courseID)
	if err != nil {
		return nil, err
	}
	if !ValidID(lessonID) || !slices.ContainsFunc(c.Lessons, func(l LessonSummary) bool { return l.ID == lessonID }) {
		return nil, ErrNotFound
	}
	return loadLesson(c, lessonID)
}

func loadCourse(root Root, id string) (*Course, error) {
	dir := filepath.Join(root.Path, id)
	raw, err := os.ReadFile(filepath.Join(dir, "course.json"))
	if errors.Is(err, os.ErrNotExist) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	c := &Course{ID: id, Source: root.Source, Dir: dir, Lessons: []LessonSummary{}}
	var cf courseFile
	if err := json.Unmarshal(raw, &cf); err != nil {
		c.Title = id
		c.Problems = append(c.Problems, "course.json: "+err.Error())
		return c, nil
	}
	c.Title, c.Description, c.Author, c.Version, c.Language = cf.Title, cf.Description, cf.Author, cf.Version, cf.Language
	if c.Title == "" {
		c.Title = id
	}

	ids := cf.Lessons
	if len(ids) == 0 {
		entries, _ := os.ReadDir(dir)
		for _, e := range entries {
			if e.IsDir() && ValidID(e.Name()) {
				ids = append(ids, e.Name()) // ReadDir is sorted by name
			}
		}
	}
	for _, lid := range ids {
		if !ValidID(lid) {
			c.Problems = append(c.Problems, fmt.Sprintf("invalid lesson id %q in course.json", lid))
			continue
		}
		l, err := loadLesson(c, lid)
		if err != nil {
			c.Problems = append(c.Problems, fmt.Sprintf("lesson %q: %v", lid, err))
			continue
		}
		c.Lessons = append(c.Lessons, l.LessonSummary)
	}
	return c, nil
}

func loadLesson(c *Course, id string) (*Lesson, error) {
	dir := filepath.Join(c.Dir, id)
	if fi, err := os.Stat(dir); err != nil || !fi.IsDir() {
		return nil, fmt.Errorf("folder missing")
	}
	l := &Lesson{CourseID: c.ID, Dir: dir}
	l.ID = id
	l.Kind = KindCode
	l.Language = c.Language

	if raw, err := os.ReadFile(filepath.Join(dir, "config.json")); err == nil {
		var cfg lessonConfig
		if err := json.Unmarshal(raw, &cfg); err != nil {
			l.Problems = append(l.Problems, "config.json: "+err.Error())
		} else {
			l.Title, l.TimeoutMs, l.MaxLatencyMs, l.Questions = cfg.Title, cfg.TimeoutMs, cfg.MaxLatencyMs, cfg.Questions
			l.Capabilities, l.MaxBudget = cfg.Capabilities, cfg.MaxBudget
			if len(l.Questions) == 0 && len(cfg.Options) > 0 {
				l.Questions = []QuizQuestion{{Options: cfg.Options}}
			}
			if cfg.Language != "" {
				l.Language = cfg.Language
			}
			if cfg.Type != "" {
				l.Kind = cfg.Type
			}
		}
	}

	if md, err := os.ReadFile(filepath.Join(dir, "lesson.md")); err == nil {
		l.Markdown = string(md)
	} else {
		l.Problems = append(l.Problems, "lesson.md is missing")
	}
	if l.Title == "" {
		l.Title = firstHeading(l.Markdown, id)
	}

	switch l.Kind {
	case KindCode:
	case KindSystemDesign:
		l.Language = ""
		if b, err := os.ReadFile(filepath.Join(dir, "starter.json")); err == nil {
			if !json.Valid(b) {
				l.Problems = append(l.Problems, "starter.json is not valid JSON")
			}
			l.Starter = string(b)
		}
		if p := filepath.Join(dir, "solution.json"); fileExists(p) {
			l.ReferenceFile = p
		}
		return l, nil
	case KindArticle:
		l.Language = ""
		return l, nil
	case KindQuiz:
		l.Language = ""
		if len(l.Questions) == 0 {
			l.Problems = append(l.Problems, `quiz needs "questions" (or "options") in config.json`)
		}
		for i, q := range l.Questions {
			if len(q.Options) < 2 {
				l.Problems = append(l.Problems, fmt.Sprintf("question %d needs at least two options", i+1))
			}
		}
		p := filepath.Join(dir, "solution.json")
		if !fileExists(p) {
			l.Problems = append(l.Problems, "solution.json is missing")
			return l, nil
		}
		l.ReferenceFile = p
		answers, err := ReadQuizAnswers(p)
		switch {
		case err != nil:
			l.Problems = append(l.Problems, "solution.json: "+err.Error())
		case len(answers) != len(l.Questions):
			l.Problems = append(l.Problems, fmt.Sprintf("solution.json has %d answers for %d questions", len(answers), len(l.Questions)))
		default:
			for i, a := range answers {
				if a.CorrectIndex >= len(l.Questions[i].Options) {
					l.Problems = append(l.Problems, fmt.Sprintf("solution.json: question %d's correct_index %d is out of range", i+1, a.CorrectIndex))
				}
			}
		}
		return l, nil
	default:
		l.Problems = append(l.Problems, fmt.Sprintf("unknown lesson type %q", l.Kind))
		return l, nil
	}
	lang, ok := runner.Lookup(l.Language)
	if !ok {
		l.Problems = append(l.Problems, fmt.Sprintf("unknown language %q (set it in course.json or config.json)", l.Language))
		return l, nil
	}
	if b, err := os.ReadFile(filepath.Join(dir, "starter"+lang.Ext)); err == nil {
		l.Starter = string(b)
	}
	if l.Capabilities.MultiFile {
		loadLessonFiles(l, dir, lang)
	}
	if p := filepath.Join(dir, "solution_test"+lang.Ext); fileExists(p) {
		l.TestFile = p
	} else {
		l.Problems = append(l.Problems, "solution_test"+lang.Ext+" is missing")
	}
	if p := filepath.Join(dir, "reference"+lang.Ext); fileExists(p) {
		l.ReferenceFile = p
	}
	return l, nil
}

// loadLessonFiles fills Files for a multi-file lesson from starter/, or
// from the single starter file if there's no starter/ folder yet.
func loadLessonFiles(l *Lesson, dir string, lang runner.Language) {
	files := map[string]string{}
	if st, err := os.Stat(filepath.Join(dir, "starter")); err == nil && st.IsDir() {
		var err error
		if files, err = ReadFileTree(filepath.Join(dir, "starter")); err != nil {
			l.Problems = append(l.Problems, "starter/: "+err.Error())
			return
		}
	} else {
		files["solution"+lang.Ext] = l.Starter
	}
	if len(files) == 0 {
		l.Problems = append(l.Problems, "starter/ has no files")
	}
	for _, ro := range l.Capabilities.ReadOnlyFiles {
		if _, ok := files[ro]; !ok {
			l.Problems = append(l.Problems, fmt.Sprintf("read-only file %q isn't in the starter files", ro))
		}
	}
	paths := make([]string, 0, len(files))
	for p := range files {
		if ReservedFilePath(p) {
			l.Problems = append(l.Problems, fmt.Sprintf("starter file name %q is reserved for the grader", p))
		}
		paths = append(paths, p)
	}
	slices.Sort(paths)
	for _, p := range paths {
		l.Files = append(l.Files, LessonFile{Path: p, Content: files[p], ReadOnly: slices.Contains(l.Capabilities.ReadOnlyFiles, p)})
	}
	if st, err := os.Stat(filepath.Join(dir, "reference")); err == nil && st.IsDir() {
		l.ReferenceDir = filepath.Join(dir, "reference")
	}
}

// ReadQuizAnswers reads a quiz's solution.json, in either form:
// {"answers": [...]} or a single {"correct_index": 0}.
func ReadQuizAnswers(path string) ([]QuizAnswer, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	type answer struct {
		CorrectIndex *int   `json:"correct_index"`
		Explanation  string `json:"explanation"`
	}
	var sol struct {
		answer
		Answers []answer `json:"answers"`
	}
	if err := json.Unmarshal(raw, &sol); err != nil {
		return nil, err
	}
	list := sol.Answers
	if list == nil {
		list = []answer{sol.answer}
	}
	out := make([]QuizAnswer, len(list))
	for i, a := range list {
		if a.CorrectIndex == nil || *a.CorrectIndex < 0 {
			return nil, fmt.Errorf(`answer %d needs a non-negative "correct_index"`, i+1)
		}
		out[i] = QuizAnswer{CorrectIndex: *a.CorrectIndex, Explanation: a.Explanation}
	}
	return out, nil
}

func firstHeading(md, fallback string) string {
	for line := range strings.Lines(md) {
		if t, ok := strings.CutPrefix(strings.TrimSpace(line), "# "); ok {
			return strings.TrimSpace(t)
		}
	}
	return fallback
}

func fileExists(p string) bool {
	fi, err := os.Stat(p)
	return err == nil && fi.Mode().IsRegular()
}
