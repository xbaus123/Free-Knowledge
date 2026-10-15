// Package progress stores learner progress in a local SQLite database:
// saved code per lesson, attempts, completions, and daily activity for
// streaks.
package progress

import (
	"database/sql"
	"errors"
	"fmt"
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
