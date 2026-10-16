package simulator

import (
	"strings"
	"testing"
)

func mix(read, write, static float64) map[string]float64 {
	return map[string]float64{ClassRead: read, ClassWrite: write, ClassStatic: static}
}

func stat(res Result, label string) (Stat, bool) {
	for _, s := range res.Stats {
		if strings.Contains(s.Label, label) {
			return s, true
		}
	}
	return Stat{}, false
}

func ptr[T any](v T) *T { return &v }

func TestCDNServesStaticFiles(t *testing.T) {
	g := graph([]string{"client:c", "cdn:edge", "loadBalancer:lb", "server:a", "server:b", "database:db"},
		"c>edge", "edge>lb", "lb>a", "lb>b", "a>db", "b>db")
	sc := Scenario{Traffic: Traffic{Requests: 2000, Mix: mix(1, 0, 1)}}
	res := runWith(t, g, Options{Scenario: sc})
	if !res.Passed {
		t.Fatalf("the CDN should take half the load off the servers: %+v", res.Issues)
	}
	served := res.Nodes["a"].Processed + res.Nodes["b"].Processed
	if served > 1100 {
		t.Errorf("servers handled %d requests; static files should mostly stop at the CDN", served)
	}
	if s, ok := stat(res, "served"); !ok || !strings.HasPrefix(s.Value, "9") {
		t.Errorf("CDN hit rate stat: %+v", res.Stats)
	}

	// Without it, the same traffic overloads two servers.
	g = graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "database:db"}, "c>lb", "lb>a", "lb>b", "a>db", "b>db")
	if res := runWith(t, g, Options{Scenario: sc}); res.Passed || !hasIssue(res, "server_overloaded") {
		t.Errorf("without a CDN the servers should be overloaded: %+v", res.Issues)
	}
}

// readHeavy has writers read their own writes back, so stale data shows.
var readHeavy = Scenario{
	Traffic: Traffic{Requests: 1000, Mix: mix(3, 1, 0), Keys: 100, ReadYourWritesMs: 20},
	Goals:   Goals{MaxStalePct: ptr(1.0)},
}

func TestReadReplicaLagCausesStaleReads(t *testing.T) {
	g := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "database:db", "replica:r"},
		"c>lb", "lb>a", "lb>b", "a>db", "b>db", "a>r", "b>r", "db>r")
	res := runWith(t, g, Options{Scenario: readHeavy})
	if res.Passed || !hasIssue(res, "stale_reads") {
		t.Fatalf("replica lag should produce stale reads: %+v", res.Issues)
	}
	for _, is := range res.Issues {
		if is.Code == "stale_reads" && (is.NodeID != "r" || !strings.Contains(is.Message, "trails the primary")) {
			t.Errorf("stale reads should be blamed on the replica: %+v", is)
		}
	}
	if res.Nodes["db"].Processed >= res.Nodes["r"].Processed {
		t.Errorf("reads should go to the replica: %+v", res.Nodes)
	}

	// A replica that isn't connected to its primary never gets data.
	g = graph([]string{"client:c", "server:a", "database:db", "replica:r"}, "c>a", "a>db", "a>r")
	if res := runWith(t, g, Options{Scenario: readHeavy}); !hasIssue(res, "replica_without_primary") {
		t.Errorf("expected replica_without_primary: %+v", res.Issues)
	}
}

func TestCachePolicies(t *testing.T) {
	g := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "cache:redis", "database:db"},
		"c>lb", "lb>a", "lb>b", "a>redis", "b>redis", "redis>db")
	ttl := runWith(t, g, Options{Scenario: readHeavy})
	if ttl.Passed || !hasIssue(ttl, "stale_reads") {
		t.Fatalf("a TTL cache keeps serving old data after writes: %+v", ttl.Issues)
	}
	node(&g, "redis").Data.Policy = "invalidate"
	inv := runWith(t, g, Options{Scenario: readHeavy})
	if !inv.Passed {
		t.Fatalf("invalidating on write keeps reads fresh: %+v %+v", inv.Issues, inv.Stats)
	}
	if s, ok := stat(inv, "hit rate"); !ok || s.Value == "0%" {
		t.Errorf("hit rate: %+v", inv.Stats)
	}
	if inv.Nodes["db"].Processed >= 1000 {
		t.Errorf("the cache should absorb reads: db processed %d", inv.Nodes["db"].Processed)
	}

	// A cache filled from a lagging replica caches stale data.
	g = graph([]string{"client:c", "server:a", "cache:redis", "database:db", "replica:r"},
		"c>a", "a>redis", "redis>r", "redis>db", "db>r")
	node(&g, "redis").Data.Policy = "invalidate"
	if res := runWith(t, g, Options{Scenario: readHeavy, MaxLatencyMs: 0}); !hasIssue(res, "stale_reads") {
		t.Errorf("filling from a replica should go stale: %+v", res.Issues)
	}
}

func TestRateLimiterStopsBots(t *testing.T) {
	sc := Scenario{Traffic: Traffic{Requests: 1000, Spikes: []Spike{{Kind: "bot", AtMs: 300, ForMs: 100, Multiplier: 50}}}}
	open := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "database:db"}, "c>lb", "lb>a", "lb>b", "a>db", "b>db")
	if res := runWith(t, open, Options{Scenario: sc, MaxLatencyMs: 200}); res.Passed {
		t.Fatal("a bot flood should swamp unprotected servers")
	}
	g := graph([]string{"client:c", "rateLimiter:rl", "loadBalancer:lb", "server:a", "server:b", "database:db"},
		"c>rl", "rl>lb", "lb>a", "lb>b", "a>db", "b>db")
	res := runWith(t, g, Options{Scenario: sc, MaxLatencyMs: 200})
	if !res.Passed {
		t.Fatalf("the rate limiter should absorb the bot: %+v", res.Issues)
	}
	if s, ok := stat(res, "Bot requests blocked"); !ok || s.Status != "good" {
		t.Errorf("bot stat: %+v", res.Stats)
	}
	if res.Metrics.Requests != 1000 {
		t.Errorf("bot requests shouldn't count as user requests: %+v", res.Metrics)
	}

	// Too strict a limit turns real users away.
	node(&g, "rl").Data.Limit = 1
	sc.Traffic.Users = 10
	if res := runWith(t, g, Options{Scenario: sc}); res.Passed || !strings.Contains(res.Message+fmtIssues(res), "real users") {
		t.Errorf("a 1 req/s limit should reject real users: %+v", res.Issues)
	}
}

func fmtIssues(res Result) string {
	var b strings.Builder
	for _, is := range res.Issues {
		b.WriteString(is.Message + "\n")
	}
	return b.String()
}

func TestQueueAcknowledgesSlowWritesQuickly(t *testing.T) {
	sc := Scenario{
		Traffic: Traffic{Requests: 1000, Mix: mix(9, 1, 0), WriteCost: 20},
		Goals:   Goals{MaxWriteMs: 50, MaxQueueLagMs: 500},
	}
	direct := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "database:db"}, "c>lb", "lb>a", "lb>b", "a>db", "b>db")
	if res := runWith(t, direct, Options{Scenario: sc}); !hasIssue(res, "slow_writes") {
		t.Fatalf("80 ms writes should miss a 50 ms target: %+v", res.Issues)
	}
	queued := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "queue:q", "database:db"},
		"c>lb", "lb>a", "lb>b", "a>db", "b>db", "a>q", "b>q", "q>db")
	node(&queued, "q").Data.Consumers = 16
	res := runWith(t, queued, Options{Scenario: sc})
	if !res.Passed {
		t.Fatalf("a queue should acknowledge writes immediately: %+v %+v", res.Issues, res.Stats)
	}
	if _, ok := stat(res, "Queue wait"); !ok {
		t.Errorf("stats: %+v", res.Stats)
	}
	// One consumer can't keep up with 100 writes/s of 80 ms each.
	node(&queued, "q").Data.Consumers = 1
	if res := runWith(t, queued, Options{Scenario: sc}); !hasIssue(res, "queue_lag") {
		t.Errorf("a single consumer should fall behind: %+v", res.Issues)
	}
	// A queue with nowhere to deliver keeps its messages.
	g := graph([]string{"client:c", "server:a", "queue:q", "database:db"}, "c>a", "a>q", "a>db")
	if res := runWith(t, g, Options{Scenario: sc}); !hasIssue(res, "queue_no_subscribers") {
		t.Errorf("expected queue_no_subscribers: %+v", res.Issues)
	}
}

// cdc is lesson 22's setup: the search index restarts mid-run.
var cdc = Scenario{
	Traffic: Traffic{Requests: 1000, Mix: mix(7, 3, 0), Keys: 100, ReadYourWritesMs: 30},
	Faults:  []Fault{{Kind: "crash", Type: TypeSearchIndex, AtMs: 300, ForMs: 300}},
	Goals:   Goals{MaxStalePct: ptr(1.0)},
}

func TestDualWritesLoseUpdates(t *testing.T) {
	g := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "cache:redis", "database:db", "searchIndex:es"},
		"c>lb", "lb>a", "lb>b", "a>redis", "b>redis", "redis>db", "a>es", "b>es")
	node(&g, "redis").Data.Policy = "invalidate"
	res := runWith(t, g, Options{Scenario: cdc})
	if res.Passed || !hasIssue(res, "index_out_of_sync") {
		t.Fatalf("dual writes during the outage should be lost: %+v", res.Issues)
	}
	if !strings.Contains(fmtIssues(res), "never retried") {
		t.Errorf("the message should explain the lost dual writes: %v", fmtIssues(res))
	}
}

func TestChangeDataCaptureKeepsIndexAndCacheInSync(t *testing.T) {
	g := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "cache:redis", "database:db", "queue:kafka", "searchIndex:es"},
		"c>lb", "lb>a", "lb>b", "a>redis", "b>redis", "redis>db", "db>kafka", "kafka>es", "kafka>redis")
	if res := runWith(t, g, Options{Scenario: cdc}); !hasIssue(res, "no_outbox") {
		t.Fatalf("without the outbox, the database publishes nothing: %+v", res.Issues)
	}
	node(&g, "db").Data.Outbox = true
	res := runWith(t, g, Options{Scenario: cdc})
	if !res.Passed {
		t.Fatalf("CDC should retry until the index catches up and invalidate the cache: %+v %+v", res.Issues, res.Stats)
	}
	if s, ok := stat(res, "es"); !ok || s.Status != "good" {
		t.Errorf("index stat: %+v", res.Stats)
	}
}

func TestPartitionsAndHotKeys(t *testing.T) {
	sc := Scenario{Traffic: Traffic{Requests: 4000, Mix: mix(1, 0, 0)}}
	g := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "server:d", "server:e", "server:f", "server:h", "server:i", "database:db"},
		"c>lb", "lb>a", "lb>b", "lb>d", "lb>e", "lb>f", "lb>h", "lb>i", "a>db", "b>db", "d>db", "e>db", "f>db", "h>db", "i>db")
	if res := runWith(t, g, Options{Scenario: sc}); !hasIssue(res, "database_overloaded") {
		t.Fatalf("4,000 queries/s should overload one database: %+v", res.Issues)
	}
	node(&g, "db").Data.Partitions = 4
	res := runWith(t, g, Options{Scenario: sc})
	if hasIssue(res, "database_overloaded") {
		t.Fatalf("four partitions should share the load: %+v", res.Issues)
	}
	if res.Cost.Total != 20+7*10+4*50 {
		t.Errorf("each partition is priced like a database: %d", res.Cost.Total)
	}
	// Everyone reading one viral record lands on one partition.
	sc.Traffic.Spikes = []Spike{{Kind: "hot_key", AtMs: 0, ForMs: 1000, Multiplier: 3}}
	sc.Traffic.Requests = 1200
	res = runWith(t, g, Options{Scenario: sc})
	if !strings.Contains(fmtIssues(res), "hot key") {
		t.Errorf("a hot key should overload its partition: %v", fmtIssues(res))
	}
}

var deploy = Scenario{
	Traffic: Traffic{Requests: 1000, Mix: mix(1, 1, 0), ClientVersions: map[string]float64{"v1": 1, "v2": 1}},
	Rollout: &Rollout{To: "v2", StartMs: 200, IntervalMs: 300, RestartMs: 200},
	Schema: &SchemaSpec{V1: []Field{
		{Tag: 1, Name: "id", Type: "int64", Required: true},
		{Tag: 2, Name: "nickname", Type: "string"},
	}, NewFields: []string{"phone"}},
}

func deployGraph(v2 ...Field) Graph {
	g := graph([]string{"client:c", "loadBalancer:lb", "server:a", "server:b", "server:d", "database:db", "schemaRegistry:reg"},
		"c>lb", "lb>a", "lb>b", "lb>d", "a>db", "b>db", "d>db")
	node(&g, "reg").Data.Fields = v2
	return g
}

func TestRollingDeployWithCompatibleSchema(t *testing.T) {
	id := Field{Tag: 1, Name: "id", Type: "int64", Required: true}
	res := runWith(t, deployGraph(id, Field{Tag: 3, Name: "phone", Type: "string"}), Options{Scenario: deploy})
	if !res.Passed {
		t.Fatalf("an optional new field is compatible both ways: %+v", res.Issues)
	}
	if s, _ := stat(res, "Rolling deploy"); s.Value != "3 of 3 servers on v2" {
		t.Errorf("rollout stat: %+v", res.Stats)
	}
	last := res.Timeline.Frames[len(res.Timeline.Frames)-1]
	if last.Nodes["a"].Badge != "v2" || res.Timeline.Frames[0].Nodes["d"].Badge != "v1" {
		t.Errorf("servers should show their version: first %+v last %+v", res.Timeline.Frames[0].Nodes, last.Nodes)
	}

	for name, tc := range map[string]struct {
		v2   []Field
		code string
	}{
		"required new field": {[]Field{id, {Tag: 3, Name: "phone", Type: "string", Required: true}}, "schema_v1_v2"},
		"reused tag":         {[]Field{id, {Tag: 2, Name: "phone", Type: "int64"}}, "schema_v1_v2"},
		"renamed tag":        {[]Field{id, {Tag: 2, Name: "phone", Type: "string"}}, "schema_v2_v1"},
		"feature missing":    {[]Field{id}, "schema_missing_phone"},
	} {
		t.Run(name, func(t *testing.T) {
			res := runWith(t, deployGraph(tc.v2...), Options{Scenario: deploy})
			if res.Passed || !hasIssue(res, tc.code) {
				t.Errorf("want %s: %+v", tc.code, res.Issues)
			}
		})
	}

	// With one server, the deploy takes the whole service down.
	g := graph([]string{"client:c", "loadBalancer:lb", "server:a", "database:db", "schemaRegistry:reg"}, "c>lb", "lb>a", "a>db")
	node(&g, "reg").Data.Fields = []Field{id, {Tag: 3, Name: "phone", Type: "string"}}
	if res := runWith(t, g, Options{Scenario: deploy}); !hasIssue(res, "no_healthy_targets") {
		t.Errorf("a single server can't be upgraded without downtime: %+v", res.Issues)
	}
}

func TestDecode(t *testing.T) {
	v1 := []Field{{Tag: 1, Name: "id", Type: "int64", Required: true}, {Tag: 2, Name: "name", Type: "string"}}
	cases := []struct {
		writer, reader []Field
		want           string
	}{
		{v1, v1, ""},
		{v1, []Field{{Tag: 1, Name: "id", Type: "int64", Required: true}}, ""}, // unknown fields are skipped
		{v1, append(v1, Field{Tag: 3, Name: "x", Type: "bool"}), ""},           // missing optional field: default
		{v1, append(v1, Field{Tag: 3, Name: "x", Type: "bool", Required: true}), "requires field"},
		{v1, []Field{{Tag: 1, Name: "id", Type: "string"}}, "can't parse"},
		{v1, []Field{{Tag: 2, Name: "title", Type: "string"}}, "silently"},
	}
	for i, c := range cases {
		got := decode(c.writer, c.reader, "v1", "v2")
		if (c.want == "") != (got == "") || !strings.Contains(got, c.want) {
			t.Errorf("%d: got %q, want %q", i, got, c.want)
		}
	}
	if validateSchema([]Field{{Tag: 1, Name: "a", Type: "int64"}, {Tag: 1, Name: "b", Type: "int64"}}) == nil {
		t.Error("duplicate tags should be rejected")
	}
}

var fencingScenario = Scenario{Kind: "fencing", Faults: []Fault{
	{Kind: "pause", Node: "a", AtMs: 300, ForMs: 1500},
	{Kind: "cut", From: TypeServer, To: TypeLock, AtMs: 300, ForMs: 1500},
}}

func fencingGraph(lease int, tokens, check bool) Graph {
	g := graph([]string{"server:a", "server:b", "lock:lock", "database:store"}, "a>lock", "b>lock", "a>store", "b>store")
	node(&g, "lock").Data.LeaseMs = lease
	node(&g, "lock").Data.Fencing = tokens
	node(&g, "store").Data.CheckTokens = check
	return g
}

func TestFencingTokens(t *testing.T) {
	for name, tc := range map[string]struct {
		g    Graph
		code string
	}{
		"long lease stalls":          {fencingGraph(10000, false, false), "stalled"},
		"short lease corrupts":       {fencingGraph(1000, false, false), "corrupted_write"},
		"tokens without checks":      {fencingGraph(1000, true, false), "tokens_unchecked"},
		"checks without tokens":      {fencingGraph(1000, false, true), "no_tokens"},
		"worker skips the lock":      {graph([]string{"server:a", "server:b", "lock:lock", "database:store"}, "a>lock", "a>store", "b>store"), "unlocked_writes"},
		"nothing to write to":        {graph([]string{"server:a", "server:b", "lock:lock"}, "a>lock", "b>lock"), "missing_storage"},
		"one worker isn't a contest": {graph([]string{"server:a", "lock:lock", "database:store"}, "a>lock", "a>store"), "missing_workers"},
	} {
		t.Run(name, func(t *testing.T) {
			res := runWith(t, tc.g, Options{Scenario: fencingScenario})
			if res.Passed || !hasIssue(res, tc.code) {
				t.Errorf("want %s: %+v", tc.code, res.Issues)
			}
		})
	}

	res := runWith(t, fencingGraph(1000, true, true), Options{Scenario: fencingScenario})
	if !res.Passed {
		t.Fatalf("fencing tokens should stop the stale write: %+v", res.Issues)
	}
	if s, _ := stat(res, "Stale writes rejected"); s.Value != "1" {
		t.Errorf("stats: %+v", res.Stats)
	}
	tl := res.Timeline
	if len(tl.Frames) != 60 || !frameAt(tl, 500).Nodes["a"].Down || !strings.Contains(frameAt(tl, 1200).Nodes["b"].Badge, "token 34") {
		t.Errorf("timeline: %d frames, a at 500 %+v, b at 1200 %+v", len(tl.Frames), frameAt(tl, 500).Nodes["a"], frameAt(tl, 1200).Nodes["b"])
	}
}

func TestScenarioValidation(t *testing.T) {
	bad := []Scenario{
		{Kind: "quantum"},
		{Palette: []string{"toaster"}},
		{Traffic: Traffic{Mix: map[string]float64{"delete": 1}}},
		{Traffic: Traffic{Requests: 1000000}},
		{Traffic: Traffic{Spikes: []Spike{{Kind: "bot", Multiplier: 0.5, ForMs: 10}}}},
		{Traffic: Traffic{Spikes: []Spike{{Kind: "bot", Multiplier: 1000, ForMs: 1000}}}},
		{Faults: []Fault{{Kind: "pause"}}},
		{Rollout: &Rollout{To: "v2"}},
		{Schema: &SchemaSpec{}},
		{Goals: Goals{Require: []string{"unicorn"}}},
	}
	for i, sc := range bad {
		if err := sc.Validate(); err == nil {
			t.Errorf("%d: expected an error for %+v", i, sc)
		}
	}
	if _, err := Run(twoServers(), Options{Scenario: Scenario{Traffic: Traffic{ClientVersions: map[string]float64{"v9": 1}}, Schema: deploy.Schema}}); err == nil {
		t.Error("client versions without a schema should be rejected")
	}
}

func TestRequiredNodeTypes(t *testing.T) {
	res := runWith(t, twoServers(), Options{Scenario: Scenario{Goals: Goals{Require: []string{TypeCache}}}})
	if res.Passed || !hasIssue(res, "missing_cache") || res.Message != "This design needs a Cache." {
		t.Errorf("issues: %+v", res.Issues)
	}
}
