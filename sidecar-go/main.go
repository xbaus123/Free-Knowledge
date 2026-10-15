// Command engine is the FreeKnowledge sidecar: it runs and grades user code
// for the desktop app over localhost HTTP/WebSocket.
package main

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"io"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/progress"
	"freeknowledge/engine/internal/runner"
	"freeknowledge/engine/internal/server"
)

var version = "0.1.0-dev"

func main() {
	addr := flag.String("addr", envOr("FK_ENGINE_ADDR", "127.0.0.1:14200"), "listen address (loopback only)")
	noWatchdog := flag.Bool("no-stdin-watchdog", false, "don't exit when stdin closes (for running by hand with stdin redirected)")
	flag.Parse()

	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stderr, nil)))
	if err := run(*addr, !*noWatchdog); err != nil {
		slog.Error("engine stopped", "err", err)
		os.Exit(1)
	}
}

func run(addr string, watchStdin bool) error {
	host, _, err := net.SplitHostPort(addr)
	if err != nil {
		return err
	}
	if ip := net.ParseIP(host); ip == nil || !ip.IsLoopback() {
		return errors.New("refusing to listen on non-loopback address " + addr)
	}

	token := os.Getenv("FK_ENGINE_TOKEN")
	if token == "" {
		token = randomToken()
		slog.Warn("FK_ENGINE_TOKEN not set; generated one for this session", "token", token)
	}

	runner.ExtendPath()

	// User courses come first so they can override bundled ones.
	var roots []course.Root
	if p := os.Getenv("FK_USER_COURSES"); p != "" {
		roots = append(roots, course.Root{Path: p, Source: "user"})
	}
	if p := os.Getenv("FK_BUNDLED_COURSES"); p != "" {
		roots = append(roots, course.Root{Path: p, Source: "bundled"})
	}
	if len(roots) == 0 {
		slog.Warn("FK_USER_COURSES and FK_BUNDLED_COURSES not set; no courses will be listed")
	}

	// FK_DATA_DIR holds progress.db. Without it, progress lasts until exit.
	dbPath := ":memory:"
	if dir := os.Getenv("FK_DATA_DIR"); dir != "" {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
		dbPath = filepath.Join(dir, "progress.db")
	} else {
		slog.Warn("FK_DATA_DIR not set; progress will not be saved")
	}
	store, err := progress.Open(dbPath)
	if err != nil {
		return err
	}
	defer store.Close()

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	if watchStdin {
		// The parent Tauri process holds our stdin pipe. When it exits for any
		// reason, including a crash, the OS closes the pipe and we read EOF.
		go func() {
			_, _ = io.Copy(io.Discard, os.Stdin)
			slog.Info("stdin closed; parent is gone, shutting down")
			stop()
		}()
	}

	ln, err := net.Listen("tcp", addr)
	if err != nil {
		return err
	}

	srv := &http.Server{
		Handler:           server.New(server.Config{Addr: addr, Token: token, Version: version, Courses: course.NewStore(roots), Progress: store}).Handler(),
		ReadHeaderTimeout: 5 * time.Second,
		// Request contexts derive from ctx, so shutdown kills running programs.
		BaseContext: func(net.Listener) context.Context { return ctx },
	}

	// Tells the parent we're ready to accept requests.
	_ = json.NewEncoder(os.Stdout).Encode(map[string]string{"event": "ready", "addr": addr, "version": version})

	errCh := make(chan error, 1)
	go func() { errCh <- srv.Serve(ln) }()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	return srv.Shutdown(shutdownCtx)
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func randomToken() string {
	b := make([]byte, 32)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}
