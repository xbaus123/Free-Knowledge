// Package server exposes the engine over localhost HTTP and WebSocket.
package server

import (
	"context"
	"crypto/subtle"
	"encoding/json"
	"errors"
	"log/slog"
	"net"
	"net/http"
	"strings"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"

	"freeknowledge/engine/internal/runner"
)

const maxBodyBytes = 1 << 20

// allowedOrigins are the webview origins Tauri uses per platform, plus the
// Vite dev server.
var allowedOrigins = map[string]bool{
	"tauri://localhost":       true, // macOS, Linux
	"http://tauri.localhost":  true, // Windows
	"https://tauri.localhost": true,
	"http://localhost:1420":   true, // vite dev
}

type Config struct {
	Addr    string
	Token   string
	Version string
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
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
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

// WebSocket protocol, one run per connection:
//
//	client → {"type":"run", ...runner.Request}
//	server → {"type":"output","phase":"run","stream":"stdout","data":"..."} (repeated)
//	server → {"type":"result", ...runner.Result}   or   {"type":"error","error":"..."}
//	client → {"type":"cancel"} or closing the socket kills the run.
type wsClientMsg struct {
	Type string `json:"type"`
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
	if err != nil || first.Type != "run" {
		conn.Close(websocket.StatusPolicyViolation, "expected a run message")
		return
	}

	// Any further message (cancel) or a closed socket stops the run.
	go func() {
		defer cancel()
		for {
			var msg wsClientMsg
			if err := wsjson.Read(ctx, conn, &msg); err != nil || msg.Type == "cancel" {
				return
			}
		}
	}()

	res, err := runner.Run(ctx, first.Request, func(phase runner.Phase, stream, chunk string) {
		// Called serially by the runner; a failed write means the client left,
		// which the reader goroutine will notice.
		_ = wsjson.Write(ctx, conn, wsOutputMsg{Type: "output", Phase: phase, Stream: stream, Data: chunk})
	})
	if err != nil {
		_ = wsjson.Write(ctx, conn, map[string]string{"type": "error", "error": err.Error()})
		conn.Close(websocket.StatusInternalError, "run failed")
		return
	}
	_ = wsjson.Write(ctx, conn, wsResultMsg{Type: "result", Result: res})
	conn.Close(websocket.StatusNormalClosure, "")
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(v); err != nil {
		slog.Debug("write response", "err", err)
	}
}
