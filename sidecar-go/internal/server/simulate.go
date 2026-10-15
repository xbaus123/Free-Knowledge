package server

import (
	"encoding/json"
	"log/slog"
	"net/http"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/simulator"
)

// handleSimulate runs traffic through a system design graph:
//
//	{"course": "…", "lesson": "…", "graph": {"nodes": [...], "edges": [...]}}
//
// With a lesson, its targets apply and the attempt is recorded (the graph is
// saved as the learner's work). Without one, defaults apply: a sandbox run.
func (s *Server) handleSimulate(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Course string          `json:"course"`
		Lesson string          `json:"lesson"`
		Graph  json.RawMessage `json:"graph"`
	}
	if !decodeBody(w, r, &body) {
		return
	}
	var g simulator.Graph
	if err := json.Unmarshal(body.Graph, &g); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid graph: " + err.Error()})
		return
	}

	var opts simulator.Options
	var l *course.Lesson
	if body.Course != "" || body.Lesson != "" {
		var err error
		if l, err = s.cfg.Courses.Lesson(body.Course, body.Lesson); err != nil {
			writeCourseError(w, err)
			return
		}
		if l.Kind != course.KindSystemDesign {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "not a system design lesson"})
			return
		}
		opts.MaxLatencyMs = float64(l.MaxLatencyMs)
	}

	res, err := simulator.Run(g, opts)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}
	if l != nil && s.cfg.Progress != nil && r.Context().Err() == nil {
		if err := s.cfg.Progress.RecordAttempt(l.CourseID, l.ID, string(body.Graph), res.Passed); err != nil {
			slog.Error("record attempt", "course", l.CourseID, "lesson", l.ID, "err", err)
		}
	}
	writeJSON(w, http.StatusOK, res)
}
