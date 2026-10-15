package progress

import (
	"path/filepath"
	"testing"
	"time"
)

func open(t *testing.T) *Store {
	t.Helper()
	s, err := Open(filepath.Join(t.TempDir(), "progress.db"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { s.Close() })
	return s
}

func TestCodeAndCompletion(t *testing.T) {
	s := open(t)
	if d, err := s.Lesson("c", "l"); err != nil || d.Code != nil || d.Completed {
		t.Fatalf("empty lesson: %+v %v", d, err)
	}

	must(t, s.SaveCode("c", "l", "draft"))
	must(t, s.RecordAttempt("c", "l", "wrong", false))
	must(t, s.RecordAttempt("c", "l", "right", true))
	must(t, s.RecordAttempt("c", "l", "broke it again", false))

	d, err := s.Lesson("c", "l")
	must(t, err)
	if !d.Completed || d.Attempts != 3 || *d.Code != "broke it again" {
		t.Fatalf("got %+v", d)
	}

	must(t, s.ResetCode("c", "l"))
	d, _ = s.Lesson("c", "l")
	if d.Code != nil || !d.Completed {
		t.Fatalf("reset should clear code but keep completion: %+v", d)
	}

	all, err := s.All()
	must(t, err)
	if p := all["c"]["l"]; !p.Completed || p.HasCode {
		t.Fatalf("All: %+v", all)
	}
}

func TestStreak(t *testing.T) {
	s := open(t)
	day := time.Date(2026, 3, 10, 12, 0, 0, 0, time.Local)
	for _, offset := range []int{-5, -3, -2, -1} {
		s.now = func() time.Time { return day.AddDate(0, 0, offset) }
		must(t, s.RecordAttempt("c", "l", "x", false))
	}

	s.now = func() time.Time { return day }
	if st, _ := s.Stats(); st.CurrentStreak != 3 {
		t.Fatalf("streak continuing from yesterday: want 3, got %d", st.CurrentStreak)
	}
	must(t, s.RecordAttempt("c", "l", "x", true))
	if st, _ := s.Stats(); st.CurrentStreak != 4 || st.CompletedLessons != 1 {
		t.Fatalf("after today: %+v", st)
	}
	s.now = func() time.Time { return day.AddDate(0, 0, 2) }
	if st, _ := s.Stats(); st.CurrentStreak != 0 {
		t.Fatalf("broken streak: want 0, got %d", st.CurrentStreak)
	}
}

func TestReopenKeepsData(t *testing.T) {
	path := filepath.Join(t.TempDir(), "p.db")
	s, err := Open(path)
	must(t, err)
	must(t, s.SaveCode("c", "l", "kept"))
	s.Close()

	s, err = Open(path)
	must(t, err)
	defer s.Close()
	d, _ := s.Lesson("c", "l")
	if d.Code == nil || *d.Code != "kept" {
		t.Fatalf("got %+v", d)
	}
}

func must(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}
