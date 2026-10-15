package server

import (
	"net/http"

	"freeknowledge/engine/internal/progress"
)

// Local learning telemetry. Sessions are only accepted for lessons whose
// config enables the telemetry capability; data never leaves this machine.
func (s *Server) telemetryRoutes(mux *http.ServeMux) {
	mux.Handle("GET /telemetry", s.requireToken(http.HandlerFunc(s.handleAllInsights)))
	mux.Handle("POST /courses/{course}/lessons/{lesson}/telemetry", s.requireToken(http.HandlerFunc(s.handleSaveSession)))
	mux.Handle("GET /courses/{course}/lessons/{lesson}/telemetry", s.requireToken(http.HandlerFunc(s.handleLessonInsights)))
	mux.Handle("DELETE /courses/{course}/lessons/{lesson}/telemetry", s.requireToken(http.HandlerFunc(s.handleDeleteInsights)))
}

func (s *Server) handleSaveSession(w http.ResponseWriter, r *http.Request) {
	l, ok := s.lessonFromPath(w, r)
	if !ok {
		return
	}
	if !l.Capabilities.Telemetry {
		writeJSON(w, http.StatusForbidden, map[string]string{"error": "telemetry is not enabled for this lesson"})
		return
	}
	var sess progress.Session
	if !decodeBody(w, r, &sess) {
		return
	}
	if err := s.cfg.Progress.SaveSession(l.CourseID, l.ID, sess); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleLessonInsights(w http.ResponseWriter, r *http.Request) {
	l, ok := s.lessonFromPath(w, r)
	if !ok {
		return
	}
	list, err := s.cfg.Progress.Insights(l.CourseID, l.ID)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	in := progress.Insights{CourseID: l.CourseID, LessonID: l.ID, Outcomes: map[string]int{}}
	if len(list) > 0 {
		in = list[0]
	}
	writeJSON(w, http.StatusOK, in)
}

func (s *Server) handleAllInsights(w http.ResponseWriter, r *http.Request) {
	list, err := s.cfg.Progress.Insights("", "")
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	if list == nil {
		list = []progress.Insights{}
	}
	writeJSON(w, http.StatusOK, list)
}

func (s *Server) handleDeleteInsights(w http.ResponseWriter, r *http.Request) {
	l, ok := s.lessonFromPath(w, r)
	if !ok {
		return
	}
	if err := s.cfg.Progress.DeleteInsights(l.CourseID, l.ID); err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": err.Error()})
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
