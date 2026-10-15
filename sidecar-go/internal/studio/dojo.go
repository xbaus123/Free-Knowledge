package studio

import (
	"archive/zip"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"maps"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"time"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/grader"
	"freeknowledge/engine/internal/simulator"
)

// A .dojo file is a zip of one course folder:
//
//	dojo.json                 {"format": 1, "id": "<course-id>", ...}
//	course.json
//	<lesson-id>/lesson.md, config.json, starter.*, solution_test.*, reference.*
//
// Only those names are accepted on import.
const DojoFormat = 1

// Import limits, to refuse zip bombs and junk.
const (
	maxEntries      = 2000
	maxFileBytes    = 5 << 20
	maxArchiveBytes = 50 << 20
)

var ErrValidation = errors.New("course failed validation")

type dojoManifest struct {
	Format     int       `json:"format"`
	ID         string    `json:"id"`
	Title      string    `json:"title"`
	ExportedAt time.Time `json:"exportedAt"`
	Engine     string    `json:"engine"`
}

// LessonCheck is the result of validating one lesson for publishing.
type LessonCheck struct {
	LessonID string `json:"lessonId"`
	Title    string `json:"title"`
	OK       bool   `json:"ok"`
	// Problem explains why OK is false.
	Problem string `json:"problem,omitempty"`
	// Warning flags something odd that doesn't block export.
	Warning string `json:"warning,omitempty"`
}

// LessonCheckDetail adds the full grading results for the Studio's check panel.
type LessonCheckDetail struct {
	LessonCheck
	Reference *grader.Result `json:"reference,omitempty"`
	Starter   *grader.Result `json:"starter,omitempty"`
	// System design lessons: simulator runs of solution.json and starter.json.
	ReferenceSim *simulator.Result `json:"referenceSim,omitempty"`
	StarterSim   *simulator.Result `json:"starterSim,omitempty"`
}

// CheckLesson runs the reference solution (must pass) and the starter
// (should fail, or the lesson is free) against the tests.
func (s *Studio) CheckLesson(ctx context.Context, courseID, lessonID string) (LessonCheckDetail, error) {
	l, err := s.Courses.Lesson(courseID, lessonID)
	if err != nil {
		return LessonCheckDetail{}, err
	}
	d := LessonCheckDetail{LessonCheck: LessonCheck{LessonID: l.ID, Title: l.Title}}
	switch {
	case !l.Valid():
		d.Problem = strings.Join(l.Problems, "; ")
		return d, nil
	case l.Kind == course.KindSystemDesign:
		return checkDesignLesson(l, d)
	case l.Kind != course.KindCode:
		d.OK = true
		return d, nil
	case l.ReferenceFile == "" && l.ReferenceDir == "":
		d.Problem = "add a reference solution so the tests can be checked"
		return d, nil
	}

	ref, err := grader.Validate(ctx, l, nil)
	if err != nil {
		return d, err
	}
	d.Reference = &ref
	if !ref.Passed {
		d.Problem = "the reference solution doesn't pass the tests"
		return d, nil
	}
	d.OK = true

	starter, err := grader.GradeStarter(ctx, l, nil)
	if err != nil {
		return d, err
	}
	d.Starter = &starter
	if starter.Passed {
		d.Warning = "the starter code already passes, so learners can finish without changing anything"
	}
	return d, nil
}

// checkDesignLesson simulates solution.json (must pass) and starter.json
// (should fail).
func checkDesignLesson(l *course.Lesson, d LessonCheckDetail) (LessonCheckDetail, error) {
	if l.ReferenceFile == "" {
		d.Problem = "add a solution.json so the lesson can be checked"
		return d, nil
	}
	opts := simulator.Options{MaxLatencyMs: float64(l.MaxLatencyMs), MaxBudget: l.MaxBudget}
	simulate := func(raw []byte, what string) (*simulator.Result, error) {
		var g simulator.Graph
		if err := json.Unmarshal(raw, &g); err != nil {
			return nil, fmt.Errorf("%s: %w", what, err)
		}
		res, err := simulator.Run(g, opts)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", what, err)
		}
		return &res, nil
	}

	raw, err := os.ReadFile(l.ReferenceFile)
	if err != nil {
		return d, err
	}
	if d.ReferenceSim, err = simulate(raw, "solution.json"); err != nil {
		d.Problem = err.Error()
		return d, nil
	}
	if !d.ReferenceSim.Passed {
		d.Problem = "solution.json doesn't pass the simulation: " + d.ReferenceSim.Message
		return d, nil
	}
	d.OK = true
	if l.Starter == "" {
		return d, nil
	}
	if d.StarterSim, err = simulate([]byte(l.Starter), "starter.json"); err != nil {
		d.Warning = err.Error()
	} else if d.StarterSim.Passed {
		d.Warning = "the starter diagram already passes, so learners can finish without changing anything"
	}
	return d, nil
}

// CheckCourse validates every lesson.
func (s *Studio) CheckCourse(ctx context.Context, courseID string) ([]LessonCheck, error) {
	c, err := s.Courses.Course(courseID)
	if err != nil {
		return nil, err
	}
	if len(c.Lessons) == 0 {
		return nil, errors.New("the course has no lessons")
	}
	out := make([]LessonCheck, 0, len(c.Lessons))
	for _, l := range c.Lessons {
		d, err := s.CheckLesson(ctx, courseID, l.ID)
		if err != nil {
			return nil, err
		}
		out = append(out, d.LessonCheck)
	}
	return out, nil
}

// Export validates the course and writes it to dest as a .dojo file. When
// validation fails it returns the checks along with ErrValidation.
func (s *Studio) Export(ctx context.Context, courseID, dest, engineVersion string) ([]LessonCheck, error) {
	if !filepath.IsAbs(dest) || !strings.EqualFold(filepath.Ext(dest), ".dojo") {
		return nil, errors.New("export path must be an absolute path ending in .dojo")
	}
	c, err := s.Courses.Course(courseID)
	if err != nil {
		return nil, err
	}
	checks, err := s.CheckCourse(ctx, courseID)
	if err != nil {
		return nil, err
	}
	for _, ch := range checks {
		if !ch.OK {
			return checks, ErrValidation
		}
	}

	tmp, err := os.CreateTemp(filepath.Dir(dest), ".export-*.dojo")
	if err != nil {
		return nil, err
	}
	defer os.Remove(tmp.Name())
	if err := writeDojo(tmp, c, dojoManifest{Format: DojoFormat, ID: c.ID, Title: c.Title, ExportedAt: time.Now().UTC(), Engine: engineVersion}); err != nil {
		tmp.Close()
		return nil, err
	}
	if err := tmp.Close(); err != nil {
		return nil, err
	}
	return checks, os.Rename(tmp.Name(), dest)
}

func writeDojo(w io.Writer, c *course.Course, manifest dojoManifest) error {
	zw := zip.NewWriter(w)
	add := func(name string, data []byte) error {
		f, err := zw.CreateHeader(&zip.FileHeader{Name: name, Method: zip.Deflate, Modified: manifest.ExportedAt})
		if err != nil {
			return err
		}
		_, err = f.Write(data)
		return err
	}
	m, _ := json.MarshalIndent(manifest, "", "  ")
	if err := add("dojo.json", append(m, '\n')); err != nil {
		return err
	}
	cf, err := os.ReadFile(filepath.Join(c.Dir, "course.json"))
	if err != nil {
		return err
	}
	if err := add("course.json", cf); err != nil {
		return err
	}
	for _, l := range c.Lessons {
		entries, err := os.ReadDir(filepath.Join(c.Dir, l.ID))
		if err != nil {
			return err
		}
		for _, e := range entries {
			if e.IsDir() && (e.Name() == "starter" || e.Name() == "reference") {
				tree, err := course.ReadFileTree(filepath.Join(c.Dir, l.ID, e.Name()))
				if err != nil {
					return fmt.Errorf("%s/%s: %w", l.ID, e.Name(), err)
				}
				for _, p := range slices.Sorted(maps.Keys(tree)) {
					if err := add(l.ID+"/"+e.Name()+"/"+p, []byte(tree[p])); err != nil {
						return err
					}
				}
				continue
			}
			if !e.Type().IsRegular() || !allowedLessonFile(e.Name()) {
				continue
			}
			data, err := os.ReadFile(filepath.Join(c.Dir, l.ID, e.Name()))
			if err != nil {
				return err
			}
			if err := add(l.ID+"/"+e.Name(), data); err != nil {
				return err
			}
		}
	}
	return zw.Close()
}

var lessonFilePattern = regexp.MustCompile(`^(lesson\.md|config\.json|(starter|solution_test|reference)\.(py|js|go|c|rs)|(starter|solution)\.json)$`)

func allowedLessonFile(name string) bool { return lessonFilePattern.MatchString(name) }

// ImportResult describes an imported course.
type ImportResult struct {
	ID       string   `json:"id"`
	Title    string   `json:"title"`
	Lessons  int      `json:"lessons"`
	Replaced bool     `json:"replaced"`
	Problems []string `json:"problems,omitempty"`
}

// ErrConflict means a course with the same ID exists and replace was false.
type ErrConflict struct{ ID, Title string }

func (e *ErrConflict) Error() string { return fmt.Sprintf("a course with id %q already exists", e.ID) }

// Import unpacks a .dojo file into the user course folder. It never runs the
// course's code. If the course already exists it is replaced only when
// replace is true; bundled courses are never touched (a user course with the
// same ID simply takes precedence).
func (s *Studio) Import(src string, replace bool) (ImportResult, error) {
	zr, err := zip.OpenReader(src)
	if err != nil {
		return ImportResult{}, fmt.Errorf("not a valid .dojo file: %w", err)
	}
	defer zr.Close()

	manifest, err := readManifest(&zr.Reader)
	if err != nil {
		return ImportResult{}, err
	}
	if err := os.MkdirAll(s.Root, 0o755); err != nil {
		return ImportResult{}, err
	}
	staging, err := os.MkdirTemp(s.Root, ".import-*") // dot prefix: ignored by the course list
	if err != nil {
		return ImportResult{}, err
	}
	defer os.RemoveAll(staging)

	if err := extract(&zr.Reader, filepath.Join(staging, manifest.ID)); err != nil {
		return ImportResult{}, err
	}
	imported, err := course.NewStore([]course.Root{{Path: staging, Source: "user"}}).Course(manifest.ID)
	if err != nil {
		return ImportResult{}, errors.New("the file doesn't contain a course.json")
	}
	res := ImportResult{ID: manifest.ID, Title: imported.Title, Lessons: len(imported.Lessons), Problems: imported.Problems}

	dest := filepath.Join(s.Root, manifest.ID)
	old := ""
	if _, err := os.Stat(dest); err == nil {
		if !replace {
			return res, &ErrConflict{ID: manifest.ID, Title: imported.Title}
		}
		old = filepath.Join(staging, ".replaced")
		if err := os.Rename(dest, old); err != nil {
			return res, err
		}
		res.Replaced = true
	}
	if err := os.Rename(filepath.Join(staging, manifest.ID), dest); err != nil {
		if old != "" {
			os.Rename(old, dest) // put the original back before staging is deleted
		}
		return res, err
	}
	return res, nil
}

func readManifest(zr *zip.Reader) (dojoManifest, error) {
	var m dojoManifest
	for _, f := range zr.File {
		if f.Name != "dojo.json" {
			continue
		}
		data, err := readEntry(f)
		if err != nil {
			return m, err
		}
		if err := json.Unmarshal(data, &m); err != nil {
			return m, fmt.Errorf("dojo.json: %w", err)
		}
		if m.Format != DojoFormat {
			return m, fmt.Errorf("unsupported .dojo format %d (this app reads format %d)", m.Format, DojoFormat)
		}
		if !course.ValidID(m.ID) {
			return m, fmt.Errorf("dojo.json: invalid course id %q", m.ID)
		}
		return m, nil
	}
	return m, errors.New("not a .dojo file: dojo.json is missing")
}

// extract writes the archive's course files into dir, rejecting anything
// outside the expected layout.
func extract(zr *zip.Reader, dir string) error {
	if len(zr.File) > maxEntries {
		return fmt.Errorf("archive has too many files (%d)", len(zr.File))
	}
	var total int64
	for _, f := range zr.File {
		name := f.Name
		if strings.HasPrefix(name, "__MACOSX/") || path.Base(name) == ".DS_Store" || strings.HasSuffix(name, "/") {
			continue
		}
		if err := checkEntryName(name); err != nil {
			return err
		}
		if !f.Mode().IsRegular() {
			return fmt.Errorf("unexpected non-regular file %q", name)
		}
		if name == "dojo.json" {
			continue
		}
		data, err := readEntry(f)
		if err != nil {
			return err
		}
		if total += int64(len(data)); total > maxArchiveBytes {
			return errors.New("archive is too large when unpacked")
		}
		target := filepath.Join(dir, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(target, data, 0o644); err != nil {
			return err
		}
	}
	return nil
}

func checkEntryName(name string) error {
	bad := fmt.Errorf("unexpected file %q in archive", name)
	if strings.Contains(name, "\\") || path.IsAbs(name) || path.Clean(name) != name {
		return bad
	}
	parts := strings.Split(name, "/")
	switch len(parts) {
	case 1:
		if name != "course.json" && name != "dojo.json" {
			return bad
		}
	case 2:
		if !course.ValidID(parts[0]) || !allowedLessonFile(parts[1]) {
			return bad
		}
	default:
		// Multi-file lessons: <lesson>/starter/... and <lesson>/reference/...
		if !course.ValidID(parts[0]) || (parts[1] != "starter" && parts[1] != "reference") || !course.ValidFilePath(strings.Join(parts[2:], "/")) {
			return bad
		}
	}
	return nil
}

// readEntry reads a zip entry, enforcing the size limit on the actual bytes
// rather than trusting the header.
func readEntry(f *zip.File) ([]byte, error) {
	if f.UncompressedSize64 > maxFileBytes {
		return nil, fmt.Errorf("%q is too large", f.Name)
	}
	rc, err := f.Open()
	if err != nil {
		return nil, err
	}
	defer rc.Close()
	data, err := io.ReadAll(io.LimitReader(rc, maxFileBytes+1))
	if err != nil {
		return nil, fmt.Errorf("read %q: %w", f.Name, err)
	}
	if len(data) > maxFileBytes {
		return nil, fmt.Errorf("%q is too large", f.Name)
	}
	return data, nil
}
