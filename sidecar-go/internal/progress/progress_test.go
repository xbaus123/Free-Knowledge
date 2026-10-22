package progress

import (
	"database/sql"
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

func TestTelemetry(t *testing.T) {
	s := open(t)
	day := time.Date(2026, 3, 10, 12, 0, 0, 0, time.UTC)
	first := Session{ID: "session-one", StartedAt: day, ReadingMs: 60_000, TypingMs: 30_000, Keystrokes: 120, Submissions: 2,
		Outcomes: map[string]int{"syntax_error": 1, "failed_assertion": 1}}
	must(t, s.SaveSession("c", "l", first))
	// Re-sending a session's totals replaces them.
	first.TypingMs, first.Submissions, first.Outcomes["failed_assertion"] = 40_000, 3, 2
	must(t, s.SaveSession("c", "l", first))
	must(t, s.SaveSession("c", "l", Session{ID: "session-two", StartedAt: day.Add(time.Hour), ReadingMs: 5_000, TypingMs: 10_000,
		Submissions: 1, Outcomes: map[string]int{"pass": 1}, Solved: true}))
	must(t, s.SaveSession("c", "other", Session{ID: "session-three", StartedAt: day, ReadingMs: 1}))

	got, err := s.Insights("c", "l")
	must(t, err)
	if len(got) != 1 {
		t.Fatalf("got %+v", got)
	}
	in := got[0]
	if in.Sessions != 2 || in.Submissions != 4 || in.Outcomes["failed_assertion"] != 2 || in.Outcomes["pass"] != 1 || in.Keystrokes != 120 {
		t.Fatalf("aggregate: %+v", in)
	}
	if in.TimeToSolveMs == nil || *in.TimeToSolveMs != 60_000+40_000+5_000+10_000 {
		t.Fatalf("time to solve: %v", in.TimeToSolveMs)
	}

	all, _ := s.Insights("", "")
	if len(all) != 2 {
		t.Fatalf("all lessons: %+v", all)
	}

	for _, bad := range []Session{
		{ID: "x", StartedAt: day},
		{ID: "valid-id-1", StartedAt: day, ReadingMs: -1},
		{ID: "valid-id-2", StartedAt: day, Outcomes: map[string]int{"hacked": 1}},
		{ID: "valid-id-3"},
	} {
		if err := s.SaveSession("c", "l", bad); err == nil {
			t.Errorf("expected rejection: %+v", bad)
		}
	}

	must(t, s.DeleteInsights("c", "l"))
	if got, _ := s.Insights("c", "l"); len(got) != 0 {
		t.Fatalf("after delete: %+v", got)
	}
}

func TestRenumberedSystemDesignLessonsKeepProgress(t *testing.T) {
	path := filepath.Join(t.TempDir(), "progress.db")
	// A database from before System Design 3.0 through 6.0 renumbered its
	// lessons: every rename applies in turn.
	db, err := sql.Open("sqlite", "file:"+path)
	must(t, err)
	for _, m := range migrations[:2] {
		_, err := db.Exec(m)
		must(t, err)
	}
	_, err = db.Exec(`PRAGMA user_version = 2;
		INSERT INTO lesson_progress (course_id, lesson_id, code, attempts, completed_at) VALUES
			('system-design', '07-bitcask-kv-store', 'my store', 3, 1),
			('system-design', '01-core-vocabulary', NULL, 1, 1),
			('system-design', '11-replication', NULL, 1, 1),
			('system-design', '12-replication-and-caching', '{"nodes":[]}', 2, 1),
			('other', '07-bitcask-kv-store', 'not mine', 1, NULL);
		INSERT INTO telemetry_sessions (session_id, course_id, lesson_id, started_at, updated_at)
			VALUES ('s1', 'system-design', '23-capstone', 1, 1);`)
	must(t, err)
	db.Close()

	s, err := Open(path)
	must(t, err)
	defer s.Close()
	d, err := s.Lesson("system-design", "13-bitcask-kv-store")
	must(t, err)
	if d.Code == nil || *d.Code != "my store" || d.Attempts != 3 || !d.Completed {
		t.Fatalf("progress should follow the lesson to its new id: %+v", d)
	}
	if d, _ := s.Lesson("system-design", "01-core-vocabulary"); !d.Completed {
		t.Fatalf("lesson 1 kept its id: %+v", d)
	}
	if d, _ := s.Lesson("system-design", "19-replication"); !d.Completed {
		t.Fatalf("renamed by every migration: %+v", d)
	}
	if d, _ := s.Lesson("system-design", "20-replication-lag-and-consistency"); d.Code != nil || d.Completed {
		t.Fatalf("a diagram shouldn't become the new Python lesson's code: %+v", d)
	}
	if d, _ := s.Lesson("other", "07-bitcask-kv-store"); d.Code == nil || *d.Code != "not mine" {
		t.Fatalf("other courses are untouched: %+v", d)
	}
	var lesson string
	must(t, s.db.QueryRow(`SELECT lesson_id FROM telemetry_sessions WHERE session_id = 's1'`).Scan(&lesson))
	if lesson != "37-capstone" {
		t.Fatalf("telemetry lesson = %q", lesson)
	}
}
