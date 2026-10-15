package server

import (
	"encoding/json"
	"errors"
	"net/http"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/studio"
)

func (s *Server) studioRoutes(mux *http.ServeMux) {
	h := func(pattern string, fn http.HandlerFunc) {
		mux.Handle(pattern, s.requireToken(s.requireStudio(fn)))
	}
	h("POST /studio/courses", s.handleCreateCourse)
	h("PUT /studio/courses/{course}", s.handleUpdateCourse)
	h("DELETE /studio/courses/{course}", s.handleDeleteCourse)
	h("POST /studio/courses/{course}/copy", s.handleCopyCourse)
	h("POST /studio/courses/{course}/export", s.handleExport)
	h("POST /studio/courses/{course}/lessons", s.handleCreateLesson)
	h("GET /studio/courses/{course}/lessons/{lesson}", s.handleStudioLesson)
	h("PUT /studio/courses/{course}/lessons/{lesson}", s.handleSaveLesson)
	h("DELETE /studio/courses/{course}/lessons/{lesson}", s.handleDeleteLesson)
	h("POST /studio/courses/{course}/lessons/{lesson}/check", s.handleCheckLesson)
	h("POST /studio/import", s.handleImport)
}

func (s *Server) requireStudio(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if s.cfg.Studio == nil {
			writeJSON(w, http.StatusServiceUnavailable, map[string]string{"error": "no user course folder is configured"})
			return
		}
		next(w, r)
	}
}

func decodeBody(w http.ResponseWriter, r *http.Request, v any) bool {
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, maxBodyBytes)).Decode(v); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "invalid JSON body: " + err.Error()})
		return false
	}
	return true
}

func writeStudioError(w http.ResponseWriter, err error) {
	var conflict *studio.ErrConflict
	switch {
	case errors.Is(err, course.ErrNotFound):
		writeJSON(w, http.StatusNotFound, map[string]string{"error": "not found"})
	case errors.Is(err, studio.ErrReadOnly):
		writeJSON(w, http.StatusForbidden, map[string]string{"error": err.Error()})
	case errors.As(err, &conflict):
		writeJSON(w, http.StatusConflict, map[string]string{"error": err.Error(), "id": conflict.ID, "title": conflict.Title})
	default:
		// Studio errors are mostly about the author's input.
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": err.Error()})
	}
}

func (s *Server) handleCreateCourse(w http.ResponseWriter, r *http.Request) {
	var meta studio.CourseMeta
	if !decodeBody(w, r, &meta) {
		return
	}
	id, err := s.cfg.Studio.CreateCourse(meta)
	if err != nil {
		writeStudioError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]string{"id": id})
}

func (s *Server) handleUpdateCourse(w http.ResponseWriter, r *http.Request) {
	var body struct {
		studio.CourseMeta
		Lessons []string `json:"lessons"`
	}
	if !decodeBody(w, r, &body) {
		return
	}
	if err := s.cfg.Studio.UpdateCourse(r.PathValue("course"), body.CourseMeta, body.Lessons); err != nil {
		writeStudioError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleDeleteCourse(w http.ResponseWriter, r *http.Request) {
	if err := s.cfg.Studio.DeleteCourse(r.PathValue("course")); err != nil {
		writeStudioError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleCopyCourse(w http.ResponseWriter, r *http.Request) {
	id, err := s.cfg.Studio.CopyCourse(r.PathValue("course"))
	if err != nil {
		writeStudioError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]string{"id": id})
}

func (s *Server) handleCreateLesson(w http.ResponseWriter, r *http.Request) {
	var body struct{ Title, Language string }
	if !decodeBody(w, r, &body) {
		return
	}
	id, err := s.cfg.Studio.CreateLesson(r.PathValue("course"), body.Title, body.Language)
	if err != nil {
		writeStudioError(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]string{"id": id})
}

func (s *Server) handleStudioLesson(w http.ResponseWriter, r *http.Request) {
	src, err := s.cfg.Studio.Lesson(r.PathValue("course"), r.PathValue("lesson"))
	if err != nil {
		writeStudioError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, src)
}

func (s *Server) handleSaveLesson(w http.ResponseWriter, r *http.Request) {
	var src studio.LessonSource
	if !decodeBody(w, r, &src) {
		return
	}
	src.ID = r.PathValue("lesson")
	if err := s.cfg.Studio.SaveLesson(r.PathValue("course"), src); err != nil {
		writeStudioError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleDeleteLesson(w http.ResponseWriter, r *http.Request) {
	if err := s.cfg.Studio.DeleteLesson(r.PathValue("course"), r.PathValue("lesson")); err != nil {
		writeStudioError(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (s *Server) handleCheckLesson(w http.ResponseWriter, r *http.Request) {
	d, err := s.cfg.Studio.CheckLesson(r.Context(), r.PathValue("course"), r.PathValue("lesson"))
	if err != nil {
		writeStudioError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, d)
}

func (s *Server) handleExport(w http.ResponseWriter, r *http.Request) {
	var body struct{ Path string }
	if !decodeBody(w, r, &body) {
		return
	}
	checks, err := s.cfg.Studio.Export(r.Context(), r.PathValue("course"), body.Path, s.cfg.Version)
	if errors.Is(err, studio.ErrValidation) {
		writeJSON(w, http.StatusUnprocessableEntity, map[string]any{"error": "fix the failing lessons before exporting", "checks": checks})
		return
	}
	if err != nil {
		writeStudioError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"path": body.Path, "checks": checks})
}

func (s *Server) handleImport(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Path    string
		Replace bool
	}
	if !decodeBody(w, r, &body) {
		return
	}
	res, err := s.cfg.Studio.Import(body.Path, body.Replace)
	if err != nil {
		writeStudioError(w, err)
		return
	}
	writeJSON(w, http.StatusOK, res)
}
