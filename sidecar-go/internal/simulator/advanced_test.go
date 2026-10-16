package simulator

import (
	"strings"
	"testing"
)

// twoServers is the lesson's passing design: client → LB → 2 servers → DB.
func twoServers() Graph {
	return graph(
		[]string{"client:c", "loadBalancer:lb", "server:api1", "server:api2", "database:db"},
		"c>lb", "lb>api1", "lb>api2", "api1>db", "api2>db",
	)
}

func node(g *Graph, id string) *Node {
	for i := range g.Nodes {
		if g.Nodes[i].ID == id {
			return &g.Nodes[i]
		}
	}
	panic(id)
}

func runWith(t *testing.T, g Graph, opts Options) Result {
	t.Helper()
	res, err := Run(g, opts)
	if err != nil {
		t.Fatal(err)
	}
	return res
}

func TestCostAndBudget(t *testing.T) {
	g := twoServers()
	res := runWith(t, g, Options{MaxBudget: 95})
	if res.Cost.Total != 90 || res.Cost.Budget != 95 || !res.Passed {
		t.Fatalf("within budget: cost=%+v passed=%v %v", res.Cost, res.Passed, res.Issues)
	}

	node(&g, "db").Data.Replication = "async"
	res = runWith(t, g, Options{MaxBudget: 95})
	if res.Cost.Total != 130 || res.Passed || !hasIssue(res, "over_budget") {
		t.Fatalf("over budget: cost=%d issues=%+v", res.Cost.Total, res.Issues)
	}
	if !strings.Contains(res.Message, "$130/month") || !strings.Contains(res.Message, "$95") {
		t.Errorf("message: %q", res.Message)
	}
	if res.Metrics.Completed != 1000 {
		t.Error("an over-budget design should still be simulated")
	}
}

func TestScaleUpWithPool(t *testing.T) {
	g := graph([]string{"client:c", "server:api", "database:db"}, "c>api", "api>db")
	node(&g, "api").Data.Pool = 8 // 8 / 6 ms ≈ 1,333 req/s
	res := runWith(t, g, Options{MaxLatencyMs: 200})
	if !res.Passed || res.Nodes["api"].Pool != 8 {
		t.Fatalf("a bigger pool should absorb the burst: %+v", res.Issues)
	}
	if res.Cost.Total != 10+4*10+50 {
		t.Errorf("cost: %d", res.Cost.Total)
	}
	// ...but scaling up costs more than scaling out here.
	if res := runWith(t, g, Options{MaxBudget: 95}); res.Passed {
		t.Error("scale-up should exceed a $95 budget")
	}
}

func TestSyncReplicationAddsLatency(t *testing.T) {
	g := twoServers()
	base := runWith(t, g, Options{}).Metrics.P50Ms
	node(&g, "db").Data.Replication = "sync"
	if got := runWith(t, g, Options{}).Metrics.P50Ms; got != base+SyncReplicaMs {
		t.Fatalf("p50 %v, want %v", got, base+SyncReplicaMs)
	}
}

func TestLeastConnectionsBalancesUnevenServers(t *testing.T) {
	g := twoServers()
	node(&g, "api1").Data.Pool = 1 // a weak server
	node(&g, "api2").Data.Pool = 8
	rr := runWith(t, g, Options{})
	node(&g, "lb").Data.Algorithm = "least_connections"
	lc := runWith(t, g, Options{})
	if lc.Metrics.P99Ms >= rr.Metrics.P99Ms {
		t.Fatalf("least connections should beat round robin here: %v vs %v", lc.Metrics.P99Ms, rr.Metrics.P99Ms)
	}
	if lc.Nodes["api2"].Processed <= lc.Nodes["api1"].Processed {
		t.Errorf("the bigger server should take more traffic: %+v", lc.Nodes)
	}
}

func TestChaosServerCrashWithRedundancy(t *testing.T) {
	res := runWith(t, twoServers(), Options{Chaos: Chaos{Nodes: []string{"api2"}}})
	if !res.Experiment || res.Passed {
		t.Fatalf("chaos run: experiment=%v passed=%v", res.Experiment, res.Passed)
	}
	m := res.Metrics
	// Requests sent to api2 before health checks notice fail; the rest succeed.
	if m.Failed == 0 || m.Failed > 100 || m.Completed+m.Failed != 1000 {
		t.Fatalf("failures should be limited to the detection window: %+v", m)
	}
	// The survivor now carries everything and becomes the bottleneck; the
	// timeline shows it saturating after the crash (at 300 ms).
	before := frameAt(res.Timeline, 150).Nodes["api1"]
	after := frameAt(res.Timeline, 600).Nodes["api1"]
	if before.Utilization > 0.9 || after.Utilization < 0.95 || after.Queue == 0 {
		t.Errorf("api1 before the crash %+v, after %+v", before, after)
	}
	if !frameAt(res.Timeline, 600).Nodes["api2"].Down {
		t.Error("api2 should show as down after the crash")
	}
	kinds := map[string]bool{}
	for _, e := range res.Timeline.Events {
		kinds[e.Kind] = true
	}
	if !kinds["crash"] || !kinds["errors"] || !kinds["bottleneck"] {
		t.Errorf("events: %+v", res.Timeline.Events)
	}
}

func TestChaosDatabaseFailover(t *testing.T) {
	for mode, want := range map[string]struct {
		recovers bool
		dataLoss bool
	}{
		"none":  {false, false},
		"sync":  {true, false},
		"async": {true, true},
	} {
		t.Run(mode, func(t *testing.T) {
			g := twoServers()
			node(&g, "db").Data.Replication = mode
			res := runWith(t, g, Options{Chaos: Chaos{Nodes: []string{"db"}}, Scenario: Scenario{Traffic: Traffic{Mix: map[string]float64{"read": 4, "write": 1}}}})
			lastFrame := res.Timeline.Frames[len(res.Timeline.Frames)-1]
			if recovered := lastFrame.Completed > 0 && !lastFrame.Nodes["db"].Down; recovered != want.recovers {
				t.Errorf("recovered=%v, want %v (last frame %+v)", recovered, want.recovers, lastFrame)
			}
			if hasIssue(res, "data_loss") != want.dataLoss {
				t.Errorf("data loss=%v, want %v: %+v", hasIssue(res, "data_loss"), want.dataLoss, res.Issues)
			}
			if mode == "none" && res.Metrics.Failed < 600 {
				t.Errorf("without a replica, everything after the crash fails: %+v", res.Metrics)
			}
		})
	}
}

func TestChaosCutEdge(t *testing.T) {
	res := runWith(t, twoServers(), Options{Chaos: Chaos{Edges: []string{"api1>db"}}})
	if res.Metrics.Failed == 0 || res.Passed {
		t.Fatalf("cutting a server from the database should fail its requests: %+v", res.Metrics)
	}
	cut := runWith(t, twoServers(), Options{Chaos: Chaos{Edges: []string{"lb>api1"}}})
	if cut.Metrics.Failed == 0 || cut.Metrics.Failed > 100 {
		t.Fatalf("the LB should route around a cut link after detection: %+v", cut.Metrics)
	}
}

func TestChaosValidation(t *testing.T) {
	for _, c := range []Chaos{{Nodes: []string{"nope"}}, {Edges: []string{"nope"}}, {Nodes: []string{"c"}}} {
		if _, err := Run(twoServers(), Options{Chaos: c}); err == nil {
			t.Errorf("expected error for %+v", c)
		}
	}
	bad := twoServers()
	node(&bad, "api1").Data.Pool = 99
	if _, err := Run(bad, Options{}); err == nil {
		t.Error("pool out of range should be rejected")
	}
	bad = twoServers()
	node(&bad, "db").Data.Replication = "quantum"
	if _, err := Run(bad, Options{}); err == nil {
		t.Error("unknown replication should be rejected")
	}
}

func TestTimeline(t *testing.T) {
	res := runWith(t, graph([]string{"client:c", "server:api", "database:db"}, "c>api", "api>db"), lesson)
	tl := res.Timeline
	if tl.IntervalMs <= 0 || len(tl.Frames) < 20 || len(tl.Frames) > 80 {
		t.Fatalf("frames: interval=%v count=%d", tl.IntervalMs, len(tl.Frames))
	}
	var sent, completed int
	peakQueue := 0
	for _, f := range tl.Frames {
		sent += f.Edges["c>api"]
		completed += f.Completed
		peakQueue = max(peakQueue, f.Nodes["api"].Queue)
		if u := f.Nodes["api"].Utilization; u < 0 || u > 1 {
			t.Fatalf("utilization out of range: %v", u)
		}
	}
	if sent != 1000 || completed != 1000 {
		t.Fatalf("frames should account for every request: sent=%d completed=%d", sent, completed)
	}
	if peakQueue < 100 {
		t.Errorf("the overloaded server's queue should show in the frames: peak %d", peakQueue)
	}
	mid := tl.Frames[len(tl.Frames)/3].Nodes["api"]
	if mid.Utilization < 0.95 || mid.Active != 4 {
		t.Errorf("mid-run, the server should be saturated: %+v", mid)
	}
	found := false
	for _, e := range tl.Events {
		if e.Kind == "bottleneck" && e.NodeID == "api" {
			found = true
		}
	}
	if !found {
		t.Errorf("expected a bottleneck event: %+v", tl.Events)
	}
}

func frameAt(tl Timeline, ms float64) Frame {
	return tl.Frames[int(ms/tl.IntervalMs)]
}
