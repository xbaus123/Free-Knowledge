package server

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/coder/websocket"
	"github.com/coder/websocket/wsjson"

	"freeknowledge/engine/internal/course"
	"freeknowledge/engine/internal/progress"
	"freeknowledge/engine/internal/studio"
)

const testToken = "secret"

func newTestServer(t *testing.T) (*httptest.Server, string) {
	t.Helper()
	ts := httptest.NewUnstartedServer(nil)
	ts.Start()
	addr := ts.Listener.Addr().String()
	store, err := progress.Open(":memory:")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { store.Close() })
	userRoot := t.TempDir()
	courses := course.NewStore([]course.Root{{Path: userRoot, Source: "user"}, {Path: "../../../courses", Source: "bundled"}})
	ts.Config.Handler = New(Config{
		Addr:     addr,
		Token:    testToken,
		Version:  "test",
		Courses:  courses,
		Progress: store,
		Studio:   &studio.Studio{Root: userRoot, Courses: courses},
	}).Handler()
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

func TestProgressEndpoints(t *testing.T) {
	ts, _ := newTestServer(t)
	auth := map[string]string{"Authorization": "Bearer " + testToken}
	base := "/courses/getting-started/lessons/01-python-greet/progress"

	if res := do(t, ts, "PUT", base+"/code", `{"code":"draft"}`, auth); res.StatusCode != 204 {
		t.Fatalf("save: %d", res.StatusCode)
	}
	if res := do(t, ts, "PUT", "/courses/getting-started/lessons/nope/progress/code", `{"code":"x"}`, auth); res.StatusCode != 404 {
		t.Fatalf("save to unknown lesson: %d", res.StatusCode)
	}

	var d struct {
		Code      *string
		Completed bool
		Attempts  int
	}
	res := do(t, ts, "GET", base, "", auth)
	if err := json.NewDecoder(res.Body).Decode(&d); err != nil || d.Code == nil || *d.Code != "draft" {
		t.Fatalf("get: %+v %v", d, err)
	}

	do(t, ts, "POST", "/courses/getting-started/lessons/01-python-greet/submit",
		`{"code":"def greet(name):\n    return f'Hello, {name or \"world\"}!'\n"}`, auth)
	res = do(t, ts, "GET", base, "", auth)
	if err := json.NewDecoder(res.Body).Decode(&d); err != nil || !d.Completed || d.Attempts != 1 {
		t.Fatalf("after submit: %+v %v", d, err)
	}

	var all struct {
		Stats   struct{ CurrentStreak, CompletedLessons int }
		Courses map[string]map[string]struct{ Completed bool }
	}
	res = do(t, ts, "GET", "/progress", "", auth)
	if err := json.NewDecoder(res.Body).Decode(&all); err != nil || all.Stats.CompletedLessons != 1 || all.Stats.CurrentStreak != 1 ||
		!all.Courses["getting-started"]["01-python-greet"].Completed {
		t.Fatalf("progress: %+v %v", all, err)
	}

	if res := do(t, ts, "DELETE", base+"/code", "", auth); res.StatusCode != 204 {
		t.Fatalf("reset: %d", res.StatusCode)
	}
}

func TestCancelledSubmitIsNotRecorded(t *testing.T) {
	ts, addr := newTestServer(t)
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	conn, _, err := websocket.Dial(ctx, "ws://"+addr+"/ws/run?token="+testToken,
		&websocket.DialOptions{HTTPHeader: http.Header{"Origin": {"tauri://localhost"}}})
	if err != nil {
		t.Fatal(err)
	}
	defer conn.CloseNow()

	code := "def greet(name):\n    print('started', flush=True)\n    while True: pass\n"
	if err := wsjson.Write(ctx, conn, map[string]string{"type": "submit", "course": "getting-started", "lesson": "01-python-greet", "code": code}); err != nil {
		t.Fatal(err)
	}
	// Wait until the program is running, then cancel the way the UI does.
	var msg map[string]any
	if err := wsjson.Read(ctx, conn, &msg); err != nil || msg["type"] != "output" {
		t.Fatalf("expected output, got %v %v", msg, err)
	}
	if err := wsjson.Write(ctx, conn, map[string]string{"type": "cancel"}); err != nil {
		t.Fatal(err)
	}
	conn.Close(websocket.StatusNormalClosure, "")

	auth := map[string]string{"Authorization": "Bearer " + testToken}
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		time.Sleep(200 * time.Millisecond)
		var d struct{ Attempts int }
		res := do(t, ts, "GET", "/courses/getting-started/lessons/01-python-greet/progress", "", auth)
		if err := json.NewDecoder(res.Body).Decode(&d); err != nil {
			t.Fatal(err)
		}
		if d.Attempts != 0 {
			t.Fatalf("cancelled run was recorded as an attempt")
		}
	}
}

func TestStudioEndpoints(t *testing.T) {
	ts, _ := newTestServer(t)
	auth := map[string]string{"Authorization": "Bearer " + testToken}
	decode := func(res *http.Response, v any) {
		t.Helper()
		if err := json.NewDecoder(res.Body).Decode(v); err != nil {
			t.Fatal(err)
		}
	}

	if res := do(t, ts, "POST", "/studio/courses/getting-started/lessons", `{"title":"x","language":"python"}`, auth); res.StatusCode != 403 {
		t.Fatalf("editing bundled course: %d", res.StatusCode)
	}

	var created struct{ ID string }
	res := do(t, ts, "POST", "/studio/courses", `{"title":"Studio Test"}`, auth)
	decode(res, &created)
	if res.StatusCode != 201 || created.ID != "studio-test" {
		t.Fatalf("create course: %d %+v", res.StatusCode, created)
	}
	base := "/studio/courses/" + created.ID
	res = do(t, ts, "POST", base+"/lessons", `{"title":"First","language":"python"}`, auth)
	var lesson struct{ ID string }
	decode(res, &lesson)

	// Break the reference, then export must refuse.
	res = do(t, ts, "GET", base+"/lessons/"+lesson.ID, "", auth)
	var src map[string]any
	decode(res, &src)
	src["reference"] = "def answer():\n    return 0\n"
	body, _ := json.Marshal(src)
	if res := do(t, ts, "PUT", base+"/lessons/"+lesson.ID, string(body), auth); res.StatusCode != 204 {
		t.Fatalf("save lesson: %d", res.StatusCode)
	}
	dest := t.TempDir() + "/out.dojo"
	if res := do(t, ts, "POST", base+"/export", `{"path":"`+dest+`"}`, auth); res.StatusCode != 422 {
		t.Fatalf("export with failing reference: %d", res.StatusCode)
	}

	src["reference"] = "def answer():\n    return 42\n"
	body, _ = json.Marshal(src)
	do(t, ts, "PUT", base+"/lessons/"+lesson.ID, string(body), auth)
	if res := do(t, ts, "POST", base+"/export", `{"path":"`+dest+`"}`, auth); res.StatusCode != 200 {
		t.Fatalf("export: %d", res.StatusCode)
	}
	if res := do(t, ts, "POST", "/studio/import", `{"path":"`+dest+`"}`, auth); res.StatusCode != 409 {
		t.Fatalf("import over existing course: %d", res.StatusCode)
	}
	if res := do(t, ts, "POST", "/studio/import", `{"path":"`+dest+`","replace":true}`, auth); res.StatusCode != 200 {
		t.Fatalf("import with replace: %d", res.StatusCode)
	}
}

func TestSimulateEndpoint(t *testing.T) {
	ts, _ := newTestServer(t)
	auth := map[string]string{"Authorization": "Bearer " + testToken}
	read := func(name string) string {
		b, err := os.ReadFile("../../../courses/system-design/01-scalability/" + name)
		if err != nil {
			t.Fatal(err)
		}
		return string(b)
	}
	var res struct {
		Passed  bool
		Message string
		Issues  []struct{ NodeID, Code string }
	}
	body := func(graph string) string {
		return `{"course":"system-design","lesson":"01-scalability","graph":` + graph + `}`
	}

	r := do(t, ts, "POST", "/simulate", body(read("starter.json")), auth)
	if err := json.NewDecoder(r.Body).Decode(&res); err != nil || r.StatusCode != 200 {
		t.Fatalf("starter: %d %v", r.StatusCode, err)
	}
	if res.Passed || res.Message != "Server overloaded: 100% CPU utilization. Add a Load Balancer." || res.Issues[0].NodeID != "api-1" {
		t.Fatalf("starter result: %+v", res)
	}

	r = do(t, ts, "POST", "/simulate", body(read("solution.json")), auth)
	if err := json.NewDecoder(r.Body).Decode(&res); err != nil || !res.Passed {
		t.Fatalf("solution result: %+v %v", res, err)
	}

	var p struct {
		Completed bool
		Attempts  int
		Code      *string
	}
	r = do(t, ts, "GET", "/courses/system-design/lessons/01-scalability/progress", "", auth)
	if err := json.NewDecoder(r.Body).Decode(&p); err != nil || !p.Completed || p.Attempts != 2 || p.Code == nil || !strings.Contains(*p.Code, `"lb"`) {
		t.Fatalf("progress: %+v %v", p, err)
	}

	if r := do(t, ts, "POST", "/simulate", `{"graph":{"nodes":[{"id":"x","type":"toaster"}],"edges":[]}}`, auth); r.StatusCode != 400 {
		t.Fatalf("bad node type: %d", r.StatusCode)
	}
	if r := do(t, ts, "POST", "/simulate", body(`{"nodes":[],"edges":[]}`), nil); r.StatusCode != 401 {
		t.Fatalf("no token: %d", r.StatusCode)
	}
}
