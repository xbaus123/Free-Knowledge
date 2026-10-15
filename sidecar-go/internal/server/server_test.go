package server

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"

	"freeknowledge/engine/internal/course"
)

const testToken = "secret"

func newTestServer(t *testing.T) (*httptest.Server, string) {
	t.Helper()
	ts := httptest.NewUnstartedServer(nil)
	ts.Start()
	addr := ts.Listener.Addr().String()
	ts.Config.Handler = New(Config{Addr: addr, Token: testToken, Version: "test", Courses: course.NewStore([]course.Root{{Path: "../../../courses", Source: "bundled"}})}).Handler()
	t.Cleanup(ts.Close)
	return ts, addr
}

func do(t *testing.T, ts *httptest.Server, method, path, body string, hdr map[string]string) *http.Response {
	t.Helper()
	req, _ := http.NewRequest(method, ts.URL+path, strings.NewReader(body))
	for k, v := range hdr {
		req.Header.Set(k, v)
	}
	res, err := ts.Client().Do(req)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { res.Body.Close() })
	return res
}

func TestHealthIsOpen(t *testing.T) {
	ts, _ := newTestServer(t)
	if res := do(t, ts, "GET", "/health", "", nil); res.StatusCode != 200 {
		t.Fatalf("got %d", res.StatusCode)
	}
}

func TestRunRequiresToken(t *testing.T) {
	ts, _ := newTestServer(t)
	body := `{"language":"python","code":"print(1)"}`
	if res := do(t, ts, "POST", "/run", body, nil); res.StatusCode != 401 {
		t.Fatalf("no token: got %d", res.StatusCode)
	}
	if res := do(t, ts, "POST", "/run", body, map[string]string{"Authorization": "Bearer wrong"}); res.StatusCode != 401 {
		t.Fatalf("bad token: got %d", res.StatusCode)
	}
}

func TestForeignOriginAndHostRejected(t *testing.T) {
	ts, _ := newTestServer(t)
	if res := do(t, ts, "GET", "/health", "", map[string]string{"Origin": "https://evil.example"}); res.StatusCode != 403 {
		t.Fatalf("foreign origin: got %d", res.StatusCode)
	}
	req, _ := http.NewRequest("GET", ts.URL+"/health", nil)
	req.Host = "evil.example:14200"
	res, err := ts.Client().Do(req)
	if err != nil {
		t.Fatal(err)
	}
	res.Body.Close()
	if res.StatusCode != 403 {
		t.Fatalf("foreign host: got %d", res.StatusCode)
	}
}

func TestCORSPreflightForTauriOrigin(t *testing.T) {
	ts, _ := newTestServer(t)
	res := do(t, ts, "OPTIONS", "/run", "", map[string]string{"Origin": "tauri://localhost"})
	if res.StatusCode != 204 || res.Header.Get("Access-Control-Allow-Origin") != "tauri://localhost" {
		t.Fatalf("preflight: %d %v", res.StatusCode, res.Header)
	}
}

func TestWebSocketStreamsOutput(t *testing.T) {
	ts, addr := newTestServer(t)
	_ = ts
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	conn, _, err := websocket.Dial(ctx, "ws://"+addr+"/ws/run?token="+testToken,
		&websocket.DialOptions{HTTPHeader: http.Header{"Origin": {"tauri://localhost"}}})
	if err != nil {
		t.Fatal(err)
	}
	defer conn.CloseNow()

	if err := wsjson.Write(ctx, conn, map[string]string{"type": "run", "language": "python", "code": "print('streamed')"}); err != nil {
		t.Fatal(err)
	}
	var sawOutput bool
	for {
		var msg map[string]any
		if err := wsjson.Read(ctx, conn, &msg); err != nil {
			t.Fatalf("read: %v", err)
		}
		switch msg["type"] {
		case "output":
			if strings.Contains(msg["data"].(string), "streamed") {
				sawOutput = true
			}
		case "result":
			if !sawOutput || msg["exitCode"].(float64) != 0 {
				t.Fatalf("bad result %v (sawOutput=%v)", msg, sawOutput)
			}
			return
		default:
			t.Fatalf("unexpected message %v", msg)
		}
	}
}

func TestCourseEndpoints(t *testing.T) {
	ts, _ := newTestServer(t)
	auth := map[string]string{"Authorization": "Bearer " + testToken}

	if res := do(t, ts, "GET", "/courses", "", auth); res.StatusCode != 200 {
		t.Fatalf("list: %d", res.StatusCode)
	}
	res := do(t, ts, "GET", "/courses/getting-started/lessons/01-python-greet", "", auth)
	var lesson map[string]any
	if err := json.NewDecoder(res.Body).Decode(&lesson); err != nil || res.StatusCode != 200 {
		t.Fatalf("lesson: %d %v", res.StatusCode, err)
	}
	for _, hidden := range []string{"testFile", "referenceFile", "dir", "TestFile"} {
		if _, ok := lesson[hidden]; ok {
			t.Errorf("lesson leaks %s", hidden)
		}
	}
	if res := do(t, ts, "GET", "/courses/getting-started/lessons/..%2F..%2Fetc", "", auth); res.StatusCode != 404 {
		t.Errorf("traversal: %d", res.StatusCode)
	}

	res = do(t, ts, "POST", "/courses/getting-started/lessons/01-python-greet/submit",
		`{"code":"def greet(name):\n    return f'Hello, {name or \"world\"}!'\n"}`, auth)
	var grade struct {
		Passed bool
		Tests  []struct{ Name, Status string }
	}
	if err := json.NewDecoder(res.Body).Decode(&grade); err != nil || !grade.Passed || len(grade.Tests) != 2 {
		t.Fatalf("submit: %d %+v %v", res.StatusCode, grade, err)
	}
}
