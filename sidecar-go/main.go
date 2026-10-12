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
	"syscall"
	"time"

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
		Handler:           server.New(server.Config{Addr: addr, Token: token, Version: version}).Handler(),
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
