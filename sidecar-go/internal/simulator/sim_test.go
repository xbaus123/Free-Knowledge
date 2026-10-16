package simulator

import (
	"strings"
	"testing"
)

// graph builds a Graph from "type:id" nodes and "a>b" edges.
func graph(nodes []string, edges ...string) Graph {
	var g Graph
	for _, spec := range nodes {
		typ, id, _ := strings.Cut(spec, ":")
		n := Node{ID: id, Type: typ}
		n.Data.Label = id
		g.Nodes = append(g.Nodes, n)
	}
	for _, e := range edges {
		src, dst, _ := strings.Cut(e, ">")
		g.Edges = append(g.Edges, Edge{ID: e, Source: src, Target: dst})
	}
	return g
}

var lesson = Options{Requests: 1000, DurationMs: 1000, MaxLatencyMs: 200}

func run(t *testing.T, g Graph) Result {
	t.Helper()
	res, err := Run(g, lesson)
	if err != nil {
		t.Fatal(err)
	}
	return res
}

func hasIssue(res Result, code string) bool {
	for _, is := range res.Issues {
		if is.Code == code {
			return true
		}
	}
	return false
}

func TestSingleServerIsOverloaded(t *testing.T) {
	res := run(t, graph([]string{"client:c", "server:api", "database:db"}, "c>api", "api>db"))
	if res.Passed {
		t.Fatal("single server should fail")
	}
	if res.Message != "Server overloaded: 100% CPU utilization. Add a Load Balancer." {
		t.Fatalf("message: %q", res.Message)
	}
	if res.Issues[0].NodeID != "api" || res.Nodes["api"].Utilization < 0.99 {
		t.Fatalf("issues %+v stats %+v", res.Issues, res.Nodes["api"])
	}
	if !hasIssue(res, "latency") || res.Metrics.P99Ms <= 200 {
		t.Fatalf("expected queueing to blow the latency target: %+v", res.Metrics)
	}
	if res.Metrics.Completed != 1000 {
		t.Fatalf("every request should eventually complete: %+v", res.Metrics)
	}
}

func TestLoadBalancedServersPass(t *testing.T) {
	res := run(t, graph(
		[]string{"client:c", "loadBalancer:lb", "server:api1", "server:api2", "database:db"},
		"c>lb", "lb>api1", "lb>api2", "api1>db", "api2>db",
	))
	if !res.Passed {
		t.Fatalf("should pass: %+v", res.Issues)
	}
	m := res.Metrics
	// client→lb→api→db and back: 6 hops × 2 ms + 1 + 6 + 4 ms of work.
	if m.P50Ms != 23 || m.P99Ms > 30 || m.Completed != 1000 || m.Failed != 0 {
		t.Fatalf("metrics: %+v", m)
	}
	if u := res.Nodes["api1"].Utilization; u < 0.6 || u > 0.9 {
		t.Fatalf("api1 utilization %.2f", u)
	}
	if res.Nodes["api1"].Processed != 500 || res.Nodes["api2"].Processed != 500 {
		t.Fatalf("round robin split: %+v %+v", res.Nodes["api1"], res.Nodes["api2"])
	}
	if res.Message != "Handled 1,000 requests with p99 latency of 23 ms." {
		t.Fatalf("message: %q", res.Message)
	}
}

func TestLoadBalancerWithOneServerStillOverloaded(t *testing.T) {
	res := run(t, graph([]string{"client:c", "loadBalancer:lb", "server:api", "database:db"}, "c>lb", "lb>api", "api>db"))
	if res.Passed || !strings.Contains(res.Message, "Add another server behind the load balancer") {
		t.Fatalf("got %q", res.Message)
	}
}

func TestThreeServersAlsoPass(t *testing.T) {
	res := run(t, graph(
		[]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "server:d", "database:db"},
		"c>lb", "lb>a", "lb>b", "lb>d", "a>db", "b>db", "d>db",
	))
	if !res.Passed {
		t.Fatalf("any design with enough capacity should pass: %+v", res.Issues)
	}
}

func TestStructuralProblems(t *testing.T) {
	cases := map[string]struct {
		g    Graph
		code string
	}{
		"no client":           {graph([]string{"server:api"}), "no_client"},
		"two clients":         {graph([]string{"client:a", "client:b", "server:api"}, "a>api", "b>api"), "multiple_clients"},
		"disconnected":        {graph([]string{"client:c", "server:api"}), "client_disconnected"},
		"empty lb":            {graph([]string{"client:c", "loadBalancer:lb"}, "c>lb"), "dead_end"},
		"lb loop":             {graph([]string{"client:c", "loadBalancer:a", "loadBalancer:b"}, "c>a", "a>b", "b>a"), "routing_loop"},
		"client to database":  {graph([]string{"client:c", "database:db"}, "c>db"), "no_server"},
		"edge back to client": {graph([]string{"client:c", "loadBalancer:lb"}, "c>lb", "lb>c"), "loop_to_client"},
	}
	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			res := run(t, tc.g)
			if res.Passed || !hasIssue(res, tc.code) {
				t.Fatalf("want issue %q, got %+v", tc.code, res.Issues)
			}
		})
	}
}

func TestMalformedInput(t *testing.T) {
	bad := []Graph{
		graph([]string{"client:c", "toaster:t"}),
		graph([]string{"client:c", "client:c"}),
		graph([]string{"client:c"}, "c>missing"),
	}
	for _, g := range bad {
		if _, err := Run(g, lesson); err == nil {
			t.Errorf("expected error for %+v", g)
		}
	}
}

func TestServerToServerChainTerminates(t *testing.T) {
	// a→b→a: each server handles the request once, then it completes.
	res := run(t, graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b"}, "c>lb", "lb>a", "lb>b", "a>b", "b>a"))
	if res.Metrics.Completed != 1000 || res.Metrics.Failed != 0 {
		t.Fatalf("metrics: %+v issues %+v", res.Metrics, res.Issues)
	}
}
