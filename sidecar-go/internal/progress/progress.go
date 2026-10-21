// Package progress stores learner progress in a local SQLite database:
// saved code per lesson, attempts, completions, and daily activity for
// streaks.
package progress

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"regexp"
	"slices"
	"time"

	_ "modernc.org/sqlite"
)

// migrations run in order; the database's user_version records how many
// have been applied. Append only.
var migrations = []string{
	`CREATE TABLE lesson_progress (
		course_id       TEXT NOT NULL,
		lesson_id       TEXT NOT NULL,
		code            TEXT,
		code_updated_at INTEGER,
		attempts        INTEGER NOT NULL DEFAULT 0,
		completed_at    INTEGER,
		PRIMARY KEY (course_id, lesson_id)
	);
	CREATE TABLE activity (day TEXT PRIMARY KEY);`,

	// Learning telemetry: one row per lesson visit, updated as it goes.
	// Counts and durations only; never code or keystroke contents.
	`CREATE TABLE telemetry_sessions (
		session_id  TEXT PRIMARY KEY,
		course_id   TEXT NOT NULL,
		lesson_id   TEXT NOT NULL,
		started_at  INTEGER NOT NULL,
		updated_at  INTEGER NOT NULL,
		reading_ms  INTEGER NOT NULL DEFAULT 0,
		typing_ms   INTEGER NOT NULL DEFAULT 0,
		keystrokes  INTEGER NOT NULL DEFAULT 0,
		submissions INTEGER NOT NULL DEFAULT 0,
		runs        INTEGER NOT NULL DEFAULT 0,
		outcomes    TEXT NOT NULL DEFAULT '{}',
		solved      INTEGER NOT NULL DEFAULT 0
	);
	CREATE INDEX telemetry_lesson ON telemetry_sessions (course_id, lesson_id, started_at);`,

	// System Design 3.0 inserted four foundation lessons after lesson 1 and
	// renumbered the rest. Keep learners' progress on the renamed lessons.
	`CREATE TEMP TABLE renamed (old TEXT PRIMARY KEY, new TEXT NOT NULL);
	INSERT INTO renamed VALUES
		('02-back-of-the-envelope', '06-back-of-the-envelope'),
		('03-scaling-out', '07-scaling-out'),
		('04-data-models-and-apis', '08-data-models-and-apis'),
		('05-three-data-models', '09-three-data-models'),
		('06-storage-engines', '10-storage-engines'),
		('07-bitcask-kv-store', '11-bitcask-kv-store'),
		('08-compaction-and-sstables', '12-compaction-and-sstables'),
		('09-encoding-and-evolution', '13-encoding-and-evolution'),
		('10-rolling-deployment', '14-rolling-deployment'),
		('11-replication', '15-replication'),
		('12-replication-and-caching', '16-replication-and-caching'),
		('13-partitioning-and-rate-limiting', '17-partitioning-and-rate-limiting'),
		('14-consistent-hashing', '18-consistent-hashing'),
		('15-transactions', '19-transactions'),
		('16-write-skew', '20-write-skew'),
		('17-distributed-trouble', '21-distributed-trouble'),
		('18-fencing-tokens', '22-fencing-tokens'),
		('19-consistency-and-consensus', '23-consistency-and-consensus'),
		('20-raft-leader-election', '24-raft-leader-election'),
		('21-batch-and-stream-processing', '25-batch-and-stream-processing'),
		('22-change-data-capture', '26-change-data-capture'),
		('23-capstone', '27-capstone');
	UPDATE lesson_progress SET lesson_id = (SELECT new FROM renamed WHERE old = lesson_id)
		WHERE course_id = 'system-design' AND lesson_id IN (SELECT old FROM renamed);
	UPDATE telemetry_sessions SET lesson_id = (SELECT new FROM renamed WHERE old = lesson_id)
		WHERE course_id = 'system-design' AND lesson_id IN (SELECT old FROM renamed);
	DROP TABLE renamed;`,
}

type Store struct {
	db  *sql.DB
	now func() time.Time
}

// Open opens (creating if needed) the database at path. Use ":memory:" for a
// throwaway store.
func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite", "file:"+path+"?_pragma=busy_timeout(5000)&_pragma=journal_mode(WAL)&_pragma=foreign_keys(1)")
	if err != nil {
		return nil, err
	}
	// One connection: SQLite has a single writer anyway, and it keeps a
	// :memory: database from splitting across connections.
	db.SetMaxOpenConns(1)
	s := &Store{db: db, now: time.Now}
	if err := s.migrate(); err != nil {
		db.Close()
		return nil, fmt.Errorf("migrate %s: %w", path, err)
	}
	return s, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) migrate() error {
	var version int
	if err := s.db.QueryRow(`PRAGMA user_version`).Scan(&version); err != nil {
		return err
	}
	if version > len(migrations) {
		return fmt.Errorf("database is from a newer version of the app (schema %d, this build knows %d)", version, len(migrations))
	}
	for i := version; i < len(migrations); i++ {
		tx, err := s.db.Begin()
		if err != nil {
			return err
		}
		if _, err := tx.Exec(migrations[i]); err != nil {
			tx.Rollback()
			return err
		}
		if _, err := tx.Exec(fmt.Sprintf(`PRAGMA user_version = %d`, i+1)); err != nil {
			tx.Rollback()
			return err
		}
		if err := tx.Commit(); err != nil {
			return err
		}
	}
	return nil
}

type LessonProgress struct {
	Completed   bool       `json:"completed"`
	CompletedAt *time.Time `json:"completedAt,omitempty"`
	Attempts    int        `json:"attempts"`
	HasCode     bool       `json:"hasCode"`
}

// LessonDetail adds the saved code, which list views don't need.
type LessonDetail struct {
	LessonProgress
	Code          *string    `json:"code"`
	CodeUpdatedAt *time.Time `json:"codeUpdatedAt,omitempty"`
}

type Stats struct {
	CurrentStreak    int `json:"currentStreak"`
	CompletedLessons int `json:"completedLessons"`
}

func msTime(v sql.NullInt64) *time.Time {
	if !v.Valid {
		return nil
	}
	t := time.UnixMilli(v.Int64)
	return &t
}

func (s *Store) Lesson(courseID, lessonID string) (LessonDetail, error) {
	var d LessonDetail
	var code sql.NullString
	var codeAt, doneAt sql.NullInt64
	err := s.db.QueryRow(`SELECT code, code_updated_at, attempts, completed_at FROM lesson_progress
		WHERE course_id = ? AND lesson_id = ?`, courseID, lessonID).Scan(&code, &codeAt, &d.Attempts, &doneAt)
	if errors.Is(err, sql.ErrNoRows) {
		return d, nil
	}
	if err != nil {
		return d, err
	}
	if code.Valid {
		d.Code = &code.String
		d.HasCode = true
	}
	d.CodeUpdatedAt = msTime(codeAt)
	d.CompletedAt = msTime(doneAt)
	d.Completed = doneAt.Valid
	return d, nil
}

// All returns progress for every lesson with any, keyed by course then lesson.
func (s *Store) All() (map[string]map[string]LessonProgress, error) {
	rows, err := s.db.Query(`SELECT course_id, lesson_id, code IS NOT NULL, attempts, completed_at FROM lesson_progress`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[string]map[string]LessonProgress{}
	for rows.Next() {
		var courseID, lessonID string
		var p LessonProgress
		var doneAt sql.NullInt64
		if err := rows.Scan(&courseID, &lessonID, &p.HasCode, &p.Attempts, &doneAt); err != nil {
			return nil, err
		}
		p.CompletedAt = msTime(doneAt)
		p.Completed = doneAt.Valid
		if out[courseID] == nil {
			out[courseID] = map[string]LessonProgress{}
		}
		out[courseID][lessonID] = p
	}
	return out, rows.Err()
}

// SaveCode stores the learner's current code (autosave).
func (s *Store) SaveCode(courseID, lessonID, code string) error {
	_, err := s.db.Exec(`INSERT INTO lesson_progress (course_id, lesson_id, code, code_updated_at) VALUES (?, ?, ?, ?)
		ON CONFLICT (course_id, lesson_id) DO UPDATE SET code = excluded.code, code_updated_at = excluded.code_updated_at`,
		courseID, lessonID, code, s.now().UnixMilli())
	return err
}

// ResetCode forgets saved code so the lesson opens with its starter again.
// Completion is kept.
func (s *Store) ResetCode(courseID, lessonID string) error {
	_, err := s.db.Exec(`UPDATE lesson_progress SET code = NULL, code_updated_at = NULL
		WHERE course_id = ? AND lesson_id = ?`, courseID, lessonID)
	return err
}

// RecordAttempt saves a graded submission. The first passing attempt marks
// the lesson complete; later failures don't undo it.
func (s *Store) RecordAttempt(courseID, lessonID, code string, passed bool) error {
	now := s.now()
	var completedAt any
	if passed {
		completedAt = now.UnixMilli()
	}
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	if _, err := tx.Exec(`INSERT INTO lesson_progress (course_id, lesson_id, code, code_updated_at, attempts, completed_at)
		VALUES (?, ?, ?, ?, 1, ?)
		ON CONFLICT (course_id, lesson_id) DO UPDATE SET
			code = excluded.code,
			code_updated_at = excluded.code_updated_at,
			attempts = attempts + 1,
			completed_at = COALESCE(completed_at, excluded.completed_at)`,
		courseID, lessonID, code, now.UnixMilli(), completedAt); err != nil {
		return err
	}
	if _, err := tx.Exec(`INSERT OR IGNORE INTO activity (day) VALUES (?)`, now.Format(time.DateOnly)); err != nil {
		return err
	}
	return tx.Commit()
}

func (s *Store) Stats() (Stats, error) {
	var st Stats
	if err := s.db.QueryRow(`SELECT COUNT(*) FROM lesson_progress WHERE completed_at IS NOT NULL`).Scan(&st.CompletedLessons); err != nil {
		return st, err
	}
	// A streak counts consecutive days with a submission, ending today, or
	// yesterday if nothing has been submitted yet today.
	rows, err := s.db.Query(`SELECT day FROM activity ORDER BY day DESC LIMIT 1000`)
	if err != nil {
		return st, err
	}
	defer rows.Close()
	expect := s.now().Format(time.DateOnly)
	first := true
	for rows.Next() {
		var day string
		if err := rows.Scan(&day); err != nil {
			return st, err
		}
		if first && day != expect {
			expect = s.now().AddDate(0, 0, -1).Format(time.DateOnly)
		}
		first = false
		if day != expect {
			break
		}
		st.CurrentStreak++
		d, _ := time.ParseInLocation(time.DateOnly, day, time.Local)
		expect = d.AddDate(0, 0, -1).Format(time.DateOnly)
	}
	return st, rows.Err()
}

// --- learning telemetry ---

// Outcome categories for submissions.
var OutcomeKinds = []string{"pass", "syntax_error", "compile_error", "failed_assertion", "runtime_error", "timeout"}

// Session is one visit to a lesson. The client sends cumulative totals, so
// saving the same session again replaces it rather than adding to it.
type Session struct {
	ID          string         `json:"sessionId"`
	StartedAt   time.Time      `json:"startedAt"`
	ReadingMs   int64          `json:"readingMs"`
	TypingMs    int64          `json:"typingMs"`
	Keystrokes  int            `json:"keystrokes"`
	Submissions int            `json:"submissions"`
	Runs        int            `json:"runs"` // scratchpad runs
	Outcomes    map[string]int `json:"outcomes"`
	Solved      bool           `json:"solved"`
}

var sessionIDPattern = regexp.MustCompile(`^[A-Za-z0-9-]{8,64}$`)

// Validate rejects malformed or implausible sessions.
func (s Session) Validate() error {
	const day = 24 * 60 * 60 * 1000
	switch {
	case !sessionIDPattern.MatchString(s.ID):
		return errors.New("invalid sessionId")
	case s.StartedAt.IsZero():
		return errors.New("startedAt is required")
	case s.ReadingMs < 0 || s.TypingMs < 0 || s.ReadingMs > day || s.TypingMs > day:
		return errors.New("durations must be between 0 and 24 hours")
	case s.Keystrokes < 0 || s.Submissions < 0 || s.Runs < 0 || s.Keystrokes > 10_000_000 || s.Submissions > 100_000 || s.Runs > 100_000:
		return errors.New("counts out of range")
	}
	for k, v := range s.Outcomes {
		if !slices.Contains(OutcomeKinds, k) || v < 0 || v > 100_000 {
			return fmt.Errorf("invalid outcome %q", k)
		}
	}
	return nil
}

// SaveSession inserts or replaces a lesson visit's totals.
func (s *Store) SaveSession(courseID, lessonID string, sess Session) error {
	if err := sess.Validate(); err != nil {
		return err
	}
	if sess.Outcomes == nil {
		sess.Outcomes = map[string]int{}
	}
	outcomes, _ := json.Marshal(sess.Outcomes)
	_, err := s.db.Exec(`INSERT INTO telemetry_sessions
		(session_id, course_id, lesson_id, started_at, updated_at, reading_ms, typing_ms, keystrokes, submissions, runs, outcomes, solved)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT (session_id) DO UPDATE SET
			updated_at = excluded.updated_at, reading_ms = excluded.reading_ms, typing_ms = excluded.typing_ms,
			keystrokes = excluded.keystrokes, submissions = excluded.submissions, runs = excluded.runs,
			outcomes = excluded.outcomes, solved = excluded.solved
		WHERE course_id = excluded.course_id AND lesson_id = excluded.lesson_id`,
		sess.ID, courseID, lessonID, sess.StartedAt.UnixMilli(), s.now().UnixMilli(),
		sess.ReadingMs, sess.TypingMs, sess.Keystrokes, sess.Submissions, sess.Runs, string(outcomes), sess.Solved)
	return err
}

// Insights summarizes all visits to one lesson.
type Insights struct {
	CourseID    string         `json:"courseId"`
	LessonID    string         `json:"lessonId"`
	Sessions    int            `json:"sessions"`
	ReadingMs   int64          `json:"readingMs"`
	TypingMs    int64          `json:"typingMs"`
	Keystrokes  int            `json:"keystrokes"`
	Submissions int            `json:"submissions"`
	Runs        int            `json:"runs"`
	Outcomes    map[string]int `json:"outcomes"`
	FirstSeen   time.Time      `json:"firstSeen"`
	// TimeToSolveMs is active time (reading + typing) across visits up to
	// and including the first one that solved the lesson.
	TimeToSolveMs *int64 `json:"timeToSolveMs,omitempty"`
}

// Insights returns per-lesson summaries; empty IDs mean all.
func (s *Store) Insights(courseID, lessonID string) ([]Insights, error) {
	rows, err := s.db.Query(`SELECT course_id, lesson_id, started_at, reading_ms, typing_ms, keystrokes, submissions, runs, outcomes, solved
		FROM telemetry_sessions
		WHERE (? = '' OR course_id = ?) AND (? = '' OR lesson_id = ?)
		ORDER BY course_id, lesson_id, started_at`, courseID, courseID, lessonID, lessonID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Insights
	var cur *Insights
	for rows.Next() {
		var c, l, outcomes string
		var started, reading, typing int64
		var keys, subs, runs int
		var solved bool
		if err := rows.Scan(&c, &l, &started, &reading, &typing, &keys, &subs, &runs, &outcomes, &solved); err != nil {
			return nil, err
		}
		if cur == nil || cur.CourseID != c || cur.LessonID != l {
			out = append(out, Insights{CourseID: c, LessonID: l, Outcomes: map[string]int{}, FirstSeen: time.UnixMilli(started)})
			cur = &out[len(out)-1]
		}
		cur.Sessions++
		cur.ReadingMs += reading
		cur.TypingMs += typing
		cur.Keystrokes += keys
		cur.Submissions += subs
		cur.Runs += runs
		var o map[string]int
		if json.Unmarshal([]byte(outcomes), &o) == nil {
			for k, v := range o {
				cur.Outcomes[k] += v
			}
		}
		if cur.TimeToSolveMs == nil && solved {
			t := cur.ReadingMs + cur.TypingMs
			cur.TimeToSolveMs = &t
		}
	}
	return out, rows.Err()
}

// DeleteInsights erases telemetry; empty IDs mean all.
func (s *Store) DeleteInsights(courseID, lessonID string) error {
	_, err := s.db.Exec(`DELETE FROM telemetry_sessions WHERE (? = '' OR course_id = ?) AND (? = '' OR lesson_id = ?)`,
		courseID, courseID, lessonID, lessonID)
	return err
}
