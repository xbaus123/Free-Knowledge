package studio

import (
	"context"
	"path/filepath"
	"testing"

	"freeknowledge/engine/internal/course"
)

// TestBundledCourses checks every bundled lesson the way the Studio does
// before export: reference solutions pass, and starters don't.
func TestBundledCourses(t *testing.T) {
	if testing.Short() {
		t.Skip("runs every bundled lesson's tests")
	}
	store := course.NewStore([]course.Root{{Path: filepath.Join("..", "..", "..", "courses"), Source: "bundled"}})
	st := &Studio{Courses: store}
	for _, c := range store.List() {
		if len(c.Problems) > 0 {
			t.Errorf("%s: %v", c.ID, c.Problems)
		}
		for _, l := range c.Lessons {
			t.Run(c.ID+"/"+l.ID, func(t *testing.T) {
				d, err := st.CheckLesson(context.Background(), c.ID, l.ID)
				if err != nil {
					t.Fatal(err)
				}
				if !d.OK || d.Warning != "" {
					t.Errorf("problem=%q warning=%q", d.Problem, d.Warning)
				}
				if r := d.Reference; r != nil && !r.Passed {
					t.Logf("reference output:\n%s\n%s\n%+v", r.Stdout, r.Stderr, r.Tests)
				}
				for name, r := range map[string]any{"solution": d.ReferenceSim, "starter": d.StarterSim} {
					if r != nil {
						t.Logf("%s: %+v", name, r)
					}
				}
			})
		}
	}
}
