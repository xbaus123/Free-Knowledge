// Package server exposes the engine over localhost HTTP and WebSocket.
package server

import (
	"context"
	"crypto/subtle"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/grader"
	"freeknowledge/engine/internal/progress"
	"freeknowledge/engine/internal/runner"
	"freeknowledge/engine/internal/studio"
)

const maxBodyBytes = 1 << 20

// allowedOrigins are the webview origins Tauri uses per platform, plus the
// Vite dev server.
var allowedOrigins = map[string]bool{
	"tauri://localhost":       true, // macOS, Linux
	"http://tauri.localhost":  true, // Windows
	"https://tauri.localhost": true,
	"http://localhost:1420":   true, // vite dev
	"http://localhost:1430":   true, // `npm run dev:web` (browser-only UI development)
}

type Config struct {
	Addr     string
	Token    string
	Version  string
	Courses  *course.Store
	Progress *progress.Store
	Studio   *studio.Studio // nil disables the /studio endpoints
}

type Server struct {
	cfg  Config
	port string
}

func New(cfg Config) *Server {
	_, port, _ := net.SplitHostPort(cfg.Addr)
	return &Server{cfg: cfg, port: port}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", s.handleHealth)
	mux.Handle("GET /runtimes", s.requireToken(http.HandlerFunc(s.handleRuntimes)))
	mux.Handle("POST /run", s.requireToken(http.HandlerFunc(s.handleRun)))
	mux.Handle("GET /ws/run", s.requireToken(http.HandlerFunc(s.handleRunWS)))
	mux.Handle("GET /courses", s.requireToken(http.HandlerFunc(s.handleCourses)))
	mux.Handle("GET /courses/{course}", s.requireToken(http.HandlerFunc(s.handleCourse)))
	mux.Handle("GET /courses/{course}/lessons/{lesson}", s.requireToken(http.HandlerFunc(s.handleLesson)))
	mux.Handle("POST /courses/{course}/lessons/{lesson}/submit", s.requireToken(http.HandlerFunc(s.handleSubmit)))
	mux.Handle("POST /courses/{course}/lessons/{lesson}/validate", s.requireToken(http.HandlerFunc(s.handleValidate)))
	mux.Handle("GET /progress", s.requireToken(http.HandlerFunc(s.handleProgress)))
	mux.Handle("GET /courses/{course}/lessons/{lesson}/progress", s.requireToken(http.HandlerFunc(s.handleLessonProgress)))
	mux.Handle("PUT /courses/{course}/lessons/{lesson}/progress/code", s.requireToken(http.HandlerFunc(s.handleSaveCode)))
	mux.Handle("DELETE /courses/{course}/lessons/{lesson}/progress/code", s.requireToken(http.HandlerFunc(s.handleResetCode)))
	mux.Handle("POST /simulate", s.requireToken(http.HandlerFunc(s.handleSimulate)))
	s.studioRoutes(mux)
	return s.guard(mux)
}

// guard rejects foreign Host headers (DNS rebinding) and applies CORS.
func (s *Server) guard(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Host != "127.0.0.1:"+s.port && r.Host != "localhost:"+s.port {
			http.Error(w, "forbidden host", http.StatusForbidden)
			return
		}
		if origin := r.Header.Get("Origin"); origin != "" {
			if !allowedOrigins[origin] {
				http.Error(w, "forbidden origin", http.StatusForbidden)
				return
			}
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Vary", "Origin")
		}
		if r.Method == http.MethodOptions {
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
			w.Header().Set("Access-Control-Max-Age", "600")
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// requireToken checks the bearer token. Browsers can't set headers on a
// WebSocket handshake, so the token may also arrive as ?token=.
func (s *Server) requireToken(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		got := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		if got == "" {
			got = r.URL.Query().Get("token")
		}
		if subtle.ConstantTimeCompare([]byte(got), []byte(s.cfg.Token)) != 1 {
			writeJSON(w, http.StatusUnauthorized, map[string]string{"error": "unauthorized"})
			return
		}
		next.ServeHTTP(w, r)
	})
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "version": s.cfg.Version})
}

func (s *Server) handleRuntimes(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, runner.Runtimes())
}

func (s *Server) handleRun(w http.ResponseWriter, r *http.Request) {
	var req runner.Request
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, maxBodyBytes)).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body: " + err.Error()})
		return
	}
	res, err := runner.Run(r.Context(), req, nil)
	if err != nil {
		status := http.StatusInternalServerError
		if errors.Is(err, runner.ErrUnknownLanguage) {
			status = http.StatusBadRequest
		}
		writeJSON(w, status, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, res)
}

// WebSocket protocol, one job per connection:
//
//	client → {"type":"run", ...runner.Request}
//	      or {"type":"submit","course":"…","lesson":"…","code":"…"}
//	      or {"type":"validate","course":"…","lesson":"…"}
//	server → {"type":"output","phase":"run","stream":"stdout","data":"..."} (repeated)
//	server → {"type":"result", ...runner.Result} for run,
//	         {"type":"grade", ...grader.Result} for submit/validate,
//	         or {"type":"error","error":"..."}
//	client → {"type":"cancel"} or closing the socket kills the job.
type wsClientMsg struct {
	Type   string `json:"type"`
	Course string `json:"course"`
	Lesson string `json:"lesson"`
	runner.Request
}

type wsOutputMsg struct {
	Type   string       `json:"type"`
	Phase  runner.Phase `json:"phase"`
	Stream string       `json:"stream"`
	Data   string       `json:"data"`
}

type wsResultMsg struct {
	Type string `json:"type"`
	runner.Result
}

type wsGradeMsg struct {
	Type string `json:"type"`
	grader.Result
}

func (s *Server) handleRunWS(w http.ResponseWriter, r *http.Request) {
	// Origin was already checked in guard.
	conn, err := websocket.Accept(w, r, &websocket.AcceptOptions{InsecureSkipVerify: true})
	if err != nil {
		return
	}
	defer conn.CloseNow()
	conn.SetReadLimit(maxBodyBytes)

	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	var first wsClientMsg
	readCtx, readCancel := context.WithTimeout(ctx, 10*time.Second)
	err = wsjson.Read(readCtx, conn, &first)
	readCancel()
	if err != nil {
		conn.Close(websocket.StatusPolicyViolation, "expected a job message")
		return
	}

	// Any further message (cancel) or a closed socket stops the job.
	go func() {
		defer cancel()
		for {
			var msg wsClientMsg
			if err := wsjson.Read(ctx, conn, &msg); err != nil || msg.Type == "cancel" {
				return
			}
		}
	}()

	onOutput := func(phase runner.Phase, stream, chunk string) {
		// Called serially; a failed write means the client left, which the
		// reader goroutine will notice.
		_ = wsjson.Write(ctx, conn, wsOutputMsg{Type: "output", Phase: phase, Stream: stream, Data: chunk})
	}

	var reply any
	switch first.Type {
	case "run":
		var res runner.Result
		if res, err = runner.Run(ctx, first.Request, onOutput); err == nil {
			reply = wsResultMsg{Type: "result", Result: res}
		}
	case "submit", "validate":
		var l *course.Lesson
		if l, err = s.cfg.Courses.Lesson(first.Course, first.Lesson); err == nil {
			var res grader.Result
			if first.Type == "submit" {
				res, err = grader.Grade(ctx, l, first.Code, onOutput)
				if err == nil {
					s.recordAttempt(ctx, l, first.Code, res)
				}
			} else {
				res, err = grader.Validate(ctx, l, onOutput)
			}
			if err == nil {
				reply = wsGradeMsg{Type: "grade", Result: res}
			}
		}
	default:
		conn.Close(websocket.StatusPolicyViolation, "unknown message type")
		return
	}
	if err != nil {
		_ = wsjson.Write(ctx, conn, map[string]string{"type": "error", "error": err.Error()})
		conn.Close(websocket.StatusNormalClosure, "")
		return
	}
	_ = wsjson.Write(ctx, conn, reply)
	conn.Close(websocket.StatusNormalClosure, "")
}

func (s *Server) handleCourses(w http.ResponseWriter, r *http.Request) {
	list := s.cfg.Courses.List()
	if list == nil {
		list = []course.Course{}
	}
	writeJSON(w, http.StatusOK, list)
}

func (s *Server) handleCourse(w http.ResponseWriter, r *http.Request) {
	c, err := s.cfg.Courses.Course(r.PathValue("course"))
	if err != nil {
		writeCourseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, c)
}

func (s *Server) handleLesson(w http.ResponseWriter, r *http.Request) {
	l, err := s.cfg.Courses.Lesson(r.PathValue("course"), r.PathValue("lesson"))
	if err != nil {
		writeCourseError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, l)
}

// handleSubmit grades a submission: {"code": "..."} for code lessons,
// {"answer": 2} for quizzes, and {} for articles (marks them read).
func (s *Server) handleSubmit(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Code   string `json:"code"`
		Answer *int   `json:"answer"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, maxBodyBytes)).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body: " + err.Error()})
		return
	}
	s.grade(w, r, func(l *course.Lesson) (grader.Result, error) {
		saved := body.Code
		var res grader.Result
		var err error
		if l.Kind == course.KindQuiz {
			if body.Answer == nil {
				return res, errors.New(`quiz submissions need an "answer"`)
			}
			// Saved like code, so the quiz reopens with the last choice selected.
			saved = fmt.Sprintf(`{"answer":%d}`, *body.Answer)
			res, err = grader.GradeAnswer(l, *body.Answer)
		} else {
			res, err = grader.Grade(r.Context(), l, body.Code, nil)
		}
		if err == nil {
			s.recordAttempt(r.Context(), l, saved, res)
		}
		return res, err
	})
}

func (s *Server) handleValidate(w http.ResponseWriter, r *http.Request) {
	s.grade(w, r, func(l *course.Lesson) (grader.Result, error) {
		return grader.Validate(r.Context(), l, nil)
	})
}

func (s *Server) grade(w http.ResponseWriter, r *http.Request, fn func(*course.Lesson) (grader.Result, error)) {
	l, err := s.cfg.Courses.Lesson(r.PathValue("course"), r.PathValue("lesson"))
	if err != nil {
		writeCourseError(w, err)
		return
	}
	res, err := fn(l)
	if err != nil {
		writeJSON(w, http.StatusUnprocessableEntity, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, res)
}

// recordAttempt saves a graded submission. Runs cut short by a cancel or a
// shutdown aren't counted.
func (s *Server) recordAttempt(ctx context.Context, l *course.Lesson, code string, res grader.Result) {
	if s.cfg.Progress == nil || ctx.Err() != nil {
		return
	}
	if err := s.cfg.Progress.RecordAttempt(l.CourseID, l.ID, code, res.Passed); err != nil {
		slog.Error("record attempt", "course", l.CourseID, "lesson", l.ID, "err", err)
	}
}

func (s *Server) handleProgress(w http.ResponseWriter, r *http.Request) {
	all, err := s.cfg.Progress.All()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	stats, err := s.cfg.Progress.Stats()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"stats": stats, "courses": all})
}

// lessonFromPath checks the lesson exists so progress can't pile up for
// arbitrary IDs.
func (s *Server) lessonFromPath(w http.ResponseWriter, r *http.Request) (*course.Lesson, bool) {
	l, err := s.cfg.Courses.Lesson(r.PathValue("course"), r.PathValue("lesson"))
	if err != nil {
		writeCourseError(w, err)
		return nil, false
	}
	return l, true
}

func (s *Server) handleLessonProgress(w http.ResponseWriter, r *http.Request) {
	l, ok := s.lessonFromPath(w, r)
	if !ok {
		return
	}
	d, err := s.cfg.Progress.Lesson(l.CourseID, l.ID)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, d)
}

func (s *Server) handleSaveCode(w http.ResponseWriter, r *http.Request) {
	l, ok := s.lessonFromPath(w, r)
	if !ok {
		return
	}
	var body struct {
		Code string `json:"code"`
	}
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, maxBodyBytes)).Decode(&body); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body: " + err.Error()})
		return
	}
	if err := s.cfg.Progress.SaveCode(l.CourseID, l.ID, body.Code); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleResetCode(w http.ResponseWriter, r *http.Request) {
	l, ok := s.lessonFromPath(w, r)
	if !ok {
		return
	}
	if err := s.cfg.Progress.ResetCode(l.CourseID, l.ID); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func writeCourseError(w http.ResponseWriter, err error) {
	if errors.Is(err, course.ErrNotFound) {
		writeJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
		return
	}
	writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		slog.Debug("write response", "err", err)
	}
}
