// Package simulator runs a discrete-event traffic simulation over a system
// design graph (the React Flow nodes and edges a learner drew) and grades
// the result.
//
// Model: the Client sends a burst of requests at a steady rate. Each request
// follows edges from the client. Load balancers forward to their targets
// (round-robin or least-connections) and stop sending to targets their
// health checks find dead. Servers and databases have a pool of workers and
// a FIFO queue, so demand beyond their capacity turns into queueing delay. A
// server calls its downstream node (usually a database) after its own work.
// Every edge adds network latency in each direction.
//
// Chaos experiments crash nodes or cut edges partway through the run. A
// replicated database fails over to its replica after a short delay.
//
// Besides the summary, Run records a timeline of frames (per-node load and
// per-edge traffic) and notable events, for replaying the run.
package simulator

import (
	"container/heap"
	"fmt"
	"math"
	"slices"
)

// Node types, matching the React Flow node "type" field.
const (
	TypeClient       = "client"
	TypeLoadBalancer = "loadBalancer"
	TypeServer       = "server"
	TypeDatabase     = "database"
)

type Graph struct {
	Nodes []Node `json:"nodes"`
	Edges []Edge `json:"edges"`
}

type Node struct {
	ID   string   `json:"id"`
	Type string   `json:"type"`
	Data NodeData `json:"data"`
}

// NodeData holds a node's label and settings; zero values mean defaults.
type NodeData struct {
	Label string `json:"label"`
	// Pool is a server's connection pool: requests it serves at once.
	Pool int `json:"pool,omitempty"`
	// Replication is a database's mode: "none", "sync", or "async".
	Replication string `json:"replication,omitempty"`
	// Algorithm is a load balancer's: "round_robin" or "least_connections".
	Algorithm string `json:"algorithm,omitempty"`
}

type Edge struct {
	ID     string `json:"id"`
	Source string `json:"source"`
	Target string `json:"target"`
}

// Chaos breaks parts of the system partway through the run.
type Chaos struct {
	// Nodes crash: they stop answering, and in-flight work is lost.
	Nodes []string `json:"nodes,omitempty"`
	// Edges are cut: requests over them time out.
	Edges []string `json:"edges,omitempty"`
	// AtMs is when it happens; 0 means 30% of the way through the burst.
	AtMs float64 `json:"atMs,omitempty"`
}

func (c Chaos) Empty() bool { return len(c.Nodes) == 0 && len(c.Edges) == 0 }

// Timing constants (milliseconds).
const (
	HopMs         = 2   // one-way network latency of every edge
	DetectMs      = 100 // load balancer health checks notice a dead target
	FailoverMs    = 150 // a replica takes over from a crashed database
	TimeoutMs     = 100 // a request over a cut edge gives up
	ReplicaLagMs  = 50  // async replicas trail the primary by this much
	SyncReplicaMs = 4   // sync replication waits for the replica's ack
	maxHops       = 32  // stops requests caught in a routing loop
	maxEvents     = 60
)

type Options struct {
	Requests     int     // burst size
	DurationMs   float64 // the burst is spread evenly over this window
	MaxLatencyMs float64 // p99 target; 0 disables the check
	MaxBudget    int     // monthly cost limit; 0 disables the check
	Chaos        Chaos
}

func (o Options) withDefaults() Options {
	if o.Requests <= 0 {
		o.Requests = 1000
	}
	if o.DurationMs <= 0 {
		o.DurationMs = 1000
	}
	if o.Chaos.AtMs <= 0 {
		o.Chaos.AtMs = o.DurationMs * 0.3
	}
	return o
}

type Issue struct {
	NodeID  string `json:"nodeId,omitempty"`
	Code    string `json:"code"`
	Message string `json:"message"`
}

type Metrics struct {
	Requests     int     `json:"requests"`
	Completed    int     `json:"completed"`
	Failed       int     `json:"failed"`
	P50Ms        float64 `json:"p50Ms"`
	P95Ms        float64 `json:"p95Ms"`
	P99Ms        float64 `json:"p99Ms"`
	MaxMs        float64 `json:"maxMs"`
	DurationMs   float64 `json:"durationMs"`
	ThroughputPS float64 `json:"throughputPerSec"`
	MaxLatencyMs float64 `json:"maxLatencyMs,omitempty"`
}

type NodeStats struct {
	Type        string  `json:"type"`
	Label       string  `json:"label"`
	Processed   int     `json:"processed"`
	Utilization float64 `json:"utilization"` // 0..1, fraction of worker time busy
	MaxQueue    int     `json:"maxQueue"`
	Pool        int     `json:"pool,omitempty"`
}

type Result struct {
	Passed   bool                 `json:"passed"`
	Message  string               `json:"message"`
	Issues   []Issue              `json:"issues"`
	Metrics  Metrics              `json:"metrics"`
	Nodes    map[string]NodeStats `json:"nodes"`
	Cost     CostBreakdown        `json:"cost"`
	Timeline Timeline             `json:"timeline"`
	// Experiment is set for chaos runs, which don't count as lesson attempts.
	Experiment bool `json:"experiment,omitempty"`
}

// --- simulation state ---

type simEdge struct {
	id       string
	to       *simNode
	cutAt    float64 // when chaos cuts it; +Inf if never
	requests []float64
}

type simNode struct {
	Node
	workers   int
	serviceMs float64
	out       []*simEdge
	rr        int
	busy      int
	queue     []*request
	processed int
	maxQueue  int
	// Active window, for utilization: first service start to last finish.
	firstStart, lastDone float64
	started              bool
	// Chaos: down from downAt until upAt (failover), +Inf when not set.
	downAt, upAt float64
	// For the timeline.
	busySpans [][2]float64
	queueLog  [][2]float64 // (time, queue length) after each change
	inService []*request
	writes    []float64 // database: completion times, for async data loss
}

func (n *simNode) name() string {
	if n.Data.Label != "" {
		return n.Data.Label
	}
	return n.ID
}

func (n *simNode) isDown(t float64) bool { return t >= n.downAt && t < n.upAt }

type request struct {
	start   float64
	backMs  float64 // latency of the response's trip back to the client
	hops    int
	visited map[*simNode]bool
	failed  bool
}

type eventKind int

const (
	arrive eventKind = iota
	done
	crash
	recover
)

type event struct {
	t    float64
	seq  int
	kind eventKind
	req  *request
	node *simNode
}

type eventQueue []*event

func (q eventQueue) Len() int { return len(q) }
func (q eventQueue) Less(i, j int) bool {
	if q[i].t != q[j].t {
		return q[i].t < q[j].t
	}
	return q[i].seq < q[j].seq
}
func (q eventQueue) Swap(i, j int) { q[i], q[j] = q[j], q[i] }
func (q *eventQueue) Push(x any)   { *q = append(*q, x.(*event)) }
func (q *eventQueue) Pop() any {
	old := *q
	e := old[len(old)-1]
	*q = old[:len(old)-1]
	return e
}

type sim struct {
	events    eventQueue
	seq       int
	latencies []float64
	doneTimes []float64
	failTimes []float64
	issues    map[string]Issue // deduplicated by code+node
	log       []Event
	logged    map[string]bool
	end       float64
}

func (s *sim) schedule(t float64, kind eventKind, req *request, node *simNode) {
	s.seq++
	heap.Push(&s.events, &event{t: t, seq: s.seq, kind: kind, req: req, node: node})
}

func (s *sim) issue(node *simNode, code, msg string) {
	key := code
	if node != nil {
		key += "/" + node.ID
	}
	if _, ok := s.issues[key]; ok {
		return
	}
	is := Issue{Code: code, Message: msg}
	if node != nil {
		is.NodeID = node.ID
	}
	s.issues[key] = is
}

// event records a timeline event once per kind and subject.
func (s *sim) event(t float64, kind, nodeID, edgeID, msg string) {
	key := kind + "/" + nodeID + "/" + edgeID
	if s.logged[key] || len(s.log) >= maxEvents {
		return
	}
	s.logged[key] = true
	s.log = append(s.log, Event{T: round1(t), Kind: kind, NodeID: nodeID, EdgeID: edgeID, Message: msg})
}

func (s *sim) fail(t float64, req *request, n *simNode, why string) {
	if req.failed {
		return
	}
	req.failed = true
	s.failTimes = append(s.failTimes, t)
	s.end = max(s.end, t)
	name := ""
	if n != nil {
		name = n.ID
	}
	s.event(t, "errors", name, "", why)
}

func (s *sim) complete(t float64, req *request) {
	if req.failed {
		return
	}
	finish := t + req.backMs
	s.latencies = append(s.latencies, finish-req.start)
	s.doneTimes = append(s.doneTimes, finish)
	s.end = max(s.end, finish)
}

// forward sends req from one node to the next over an edge.
func (s *sim) forward(t float64, req *request, from *simNode, e *simEdge) {
	req.hops++
	if req.hops > maxHops {
		s.issue(from, "routing_loop", fmt.Sprintf("Requests loop forever through %s. Remove the cycle.", from.name()))
		s.fail(t, req, from, fmt.Sprintf("Requests are looping through %s", from.name()))
		return
	}
	e.requests = append(e.requests, t)
	if t >= e.cutAt {
		s.fail(t+TimeoutMs, req, from, fmt.Sprintf("Requests from %s to %s time out: the connection is cut", from.name(), e.to.name()))
		return
	}
	req.backMs += HopMs
	s.schedule(t+HopMs, arrive, req, e.to)
}

// healthy reports whether a load balancer still sends to edge e at time t:
// it stops once health checks have noticed the target or link is down.
func healthy(e *simEdge, t float64) bool {
	return !(t >= e.cutAt+DetectMs) && !(t >= e.to.downAt+DetectMs && t < e.to.upAt)
}

// pick chooses a downstream edge for node n.
func (n *simNode) pick(t float64) *simEdge {
	if n.Type != TypeLoadBalancer {
		if len(n.out) == 0 {
			return nil
		}
		e := n.out[n.rr%len(n.out)]
		n.rr++
		return e
	}
	var candidates []*simEdge
	for _, e := range n.out {
		if healthy(e, t) {
			candidates = append(candidates, e)
		}
	}
	if len(candidates) == 0 {
		return nil
	}
	if n.Data.Algorithm == "least_connections" {
		best := candidates[n.rr%len(candidates)]
		for _, e := range candidates {
			if load(e.to) < load(best.to) {
				best = e
			}
		}
		n.rr++
		return best
	}
	e := candidates[n.rr%len(candidates)]
	n.rr++
	return e
}

func load(n *simNode) int { return n.busy + len(n.queue) }

func (s *sim) handle(e *event) {
	n, req := e.node, e.req
	switch e.kind {
	case crash:
		s.crash(e.t, n)
	case recover:
		s.event(e.t, "failover", n.ID, "", fmt.Sprintf("%s's replica took over", n.name()))
	case arrive:
		if req.failed {
			return
		}
		if n.isDown(e.t) {
			s.fail(e.t, req, n, fmt.Sprintf("%s is down: requests to it fail", n.name()))
			return
		}
		switch n.Type {
		case TypeLoadBalancer:
			n.processed++
			target := n.pick(e.t)
			if target == nil {
				if len(n.out) == 0 {
					s.issue(n, "dead_end", fmt.Sprintf("%s isn't connected to any servers.", n.name()))
				} else {
					s.issue(n, "no_healthy_targets", fmt.Sprintf("%s has no healthy servers left to send traffic to.", n.name()))
				}
				s.fail(e.t, req, n, fmt.Sprintf("%s has nowhere to send requests", n.name()))
				return
			}
			s.forward(e.t+n.serviceMs, req, n, target)
		case TypeClient:
			s.issue(n, "loop_to_client", "Requests are routed back into a Client. Edges should point away from the client.")
			s.fail(e.t, req, n, "Requests are routed back into the Client")
		default:
			if n.busy < n.workers {
				s.startService(e.t, req, n)
			} else {
				n.queue = append(n.queue, req)
				n.maxQueue = max(n.maxQueue, len(n.queue))
				n.queueLog = append(n.queueLog, [2]float64{e.t, float64(len(n.queue))})
				if len(n.queue) == 10 {
					s.event(e.t, "queueing", n.ID, "", fmt.Sprintf("Requests started piling up at %s", n.name()))
				}
			}
		}
	case done:
		if !slices.Contains(n.inService, req) {
			return // lost in a crash
		}
		n.inService = slices.DeleteFunc(n.inService, func(r *request) bool { return r == req })
		n.busy--
		n.processed++
		n.lastDone = e.t
		if n.Type == TypeDatabase {
			n.writes = append(n.writes, e.t)
		}
		if len(n.queue) > 0 {
			queued := n.queue[0]
			n.queue = n.queue[1:]
			n.queueLog = append(n.queueLog, [2]float64{e.t, float64(len(n.queue))})
			s.startService(e.t, queued, n)
		}
		// Servers call their downstream (usually a database); a node only
		// handles a given request once, so A→B→A doesn't loop.
		if n.Type == TypeServer && len(n.out) > 0 {
			if target := n.pick(e.t); !req.visited[target.to] {
				s.forward(e.t, req, n, target)
				return
			}
		}
		s.complete(e.t, req)
	}
}

func (s *sim) startService(t float64, req *request, n *simNode) {
	if !n.started {
		n.started, n.firstStart = true, t
	}
	n.busy++
	n.busySpans = append(n.busySpans, [2]float64{t, t + n.serviceMs})
	n.inService = append(n.inService, req)
	req.visited[n] = true
	s.schedule(t+n.serviceMs, done, req, n)
}

// crash takes a node down: everything in flight or queued there fails.
func (s *sim) crash(t float64, n *simNode) {
	msg := fmt.Sprintf("Chaos: %s crashed", n.name())
	s.log = append(s.log, Event{T: round1(t), Kind: "crash", NodeID: n.ID, Message: msg})
	for _, r := range append(n.inService, n.queue...) {
		s.fail(t, r, n, fmt.Sprintf("Work in progress on %s was lost", n.name()))
	}
	n.inService, n.queue, n.busy = nil, nil, 0
	n.queueLog = append(n.queueLog, [2]float64{t, 0})
	// Truncate busy time at the crash.
	for i, span := range n.busySpans {
		if span[1] > t {
			n.busySpans[i][1] = max(span[0], t)
		}
	}
	if n.Type == TypeDatabase && n.Data.Replication == "async" {
		lost := 0
		for _, w := range n.writes {
			if w > t-ReplicaLagMs {
				lost++
			}
		}
		if lost > 0 {
			s.issue(n, "data_loss", fmt.Sprintf("%d writes %s had confirmed were lost: async replication hadn't copied them to the replica yet.", lost, n.name()))
			s.event(t, "data_loss", n.ID, "", fmt.Sprintf("%d confirmed writes lost in failover", lost))
		}
	}
}

// Run simulates the burst over g and grades it. It returns an error only for
// malformed input; design mistakes are reported as Issues.
func Run(g Graph, opts Options) (Result, error) {
	opts = opts.withDefaults()
	cost, err := Cost(g)
	if err != nil {
		return Result{}, err
	}
	nodes := map[string]*simNode{}
	var clients []*simNode
	for _, n := range g.Nodes {
		if n.ID == "" {
			return Result{}, fmt.Errorf("node without an id")
		}
		if _, dup := nodes[n.ID]; dup {
			return Result{}, fmt.Errorf("duplicate node id %q", n.ID)
		}
		sn := &simNode{Node: n, downAt: math.Inf(1), upAt: math.Inf(1)}
		spec := catalog[n.Type] // Cost validated the type and settings
		sn.workers, sn.serviceMs = spec.Workers, spec.ServiceMs
		switch n.Type {
		case TypeClient:
			clients = append(clients, sn)
		case TypeServer:
			if n.Data.Pool > 0 {
				sn.workers = n.Data.Pool
			}
		case TypeDatabase:
			if n.Data.Replication == "sync" {
				sn.serviceMs += SyncReplicaMs
			}
		}
		nodes[n.ID] = sn
	}
	edges := map[string]*simEdge{}
	for i, e := range g.Edges {
		from, to := nodes[e.Source], nodes[e.Target]
		if from == nil || to == nil {
			return Result{}, fmt.Errorf("edge %q connects a node that doesn't exist", e.ID)
		}
		id := e.ID
		if id == "" {
			id = fmt.Sprintf("edge-%d", i)
		}
		if from != to && !slices.ContainsFunc(from.out, func(x *simEdge) bool { return x.to == to }) {
			se := &simEdge{id: id, to: to, cutAt: math.Inf(1)}
			from.out = append(from.out, se)
			edges[id] = se
		}
	}

	s := &sim{issues: map[string]Issue{}, logged: map[string]bool{}}
	res := Result{Issues: []Issue{}, Nodes: map[string]NodeStats{}, Cost: cost, Experiment: !opts.Chaos.Empty(),
		Metrics: Metrics{Requests: opts.Requests, MaxLatencyMs: opts.MaxLatencyMs}}

	// Chaos.
	for _, id := range opts.Chaos.Nodes {
		n := nodes[id]
		if n == nil {
			return Result{}, fmt.Errorf("chaos: no node %q", id)
		}
		if n.Type == TypeClient {
			return Result{}, fmt.Errorf("chaos: the Client can't be crashed")
		}
		n.downAt = opts.Chaos.AtMs
		s.schedule(n.downAt, crash, nil, n)
		if n.Type == TypeDatabase && n.Data.Replication != "" && n.Data.Replication != "none" {
			n.upAt = n.downAt + FailoverMs
			s.schedule(n.upAt, recover, nil, n)
		}
	}
	for _, id := range opts.Chaos.Edges {
		e := edges[id]
		if e == nil {
			return Result{}, fmt.Errorf("chaos: no edge %q", id)
		}
		e.cutAt = opts.Chaos.AtMs
		s.log = append(s.log, Event{T: round1(e.cutAt), Kind: "partition", EdgeID: id, Message: fmt.Sprintf("Chaos: the connection to %s was cut", e.to.name())})
	}

	switch {
	case len(clients) == 0:
		s.issue(nil, "no_client", "Add a Client node to send traffic.")
	case len(clients) > 1:
		s.issue(nil, "multiple_clients", "Use a single Client node; it represents all of your users.")
	case len(clients[0].out) == 0:
		s.issue(clients[0], "client_disconnected", "Connect the Client to the rest of your system.")
	}
	if len(s.issues) > 0 {
		return finish(res, s, nodes, edges, opts), nil
	}

	client := clients[0]
	interval := opts.DurationMs / float64(opts.Requests)
	for i := range opts.Requests {
		t := float64(i) * interval
		req := &request{start: t, visited: map[*simNode]bool{}}
		s.forward(t, req, client, client.pick(t))
	}
	for s.events.Len() > 0 {
		s.handle(heap.Pop(&s.events).(*event))
	}
	return finish(res, s, nodes, edges, opts), nil
}

// finish computes metrics and the timeline, and grades the run.
func finish(res Result, s *sim, nodes map[string]*simNode, edges map[string]*simEdge, opts Options) Result {
	m := &res.Metrics
	m.Completed, m.Failed = len(s.latencies), len(s.failTimes)
	m.DurationMs = round1(s.end)
	slices.Sort(s.latencies)
	m.P50Ms, m.P95Ms, m.P99Ms = percentile(s.latencies, 50), percentile(s.latencies, 95), percentile(s.latencies, 99)
	if len(s.latencies) > 0 {
		m.MaxMs = round1(s.latencies[len(s.latencies)-1])
	}
	if s.end > 0 {
		m.ThroughputPS = math.Round(float64(m.Completed) / s.end * 1000)
	}

	hasLB := false
	ids := make([]string, 0, len(nodes))
	for id, n := range nodes {
		ids = append(ids, id)
		if n.Type == TypeLoadBalancer && n.processed > 0 {
			hasLB = true
		}
	}
	slices.Sort(ids) // stable issue order

	servedByServer := false
	for _, id := range ids {
		n := nodes[id]
		st := NodeStats{Type: n.Type, Label: n.name(), Processed: n.processed, MaxQueue: n.maxQueue}
		if n.Type == TypeServer || n.Type == TypeDatabase {
			st.Pool = n.workers
		}
		if window := n.lastDone - n.firstStart; n.workers > 0 && window > 0 {
			st.Utilization = math.Min(1, busyBetween(n.busySpans, n.firstStart, n.lastDone)/(float64(n.workers)*window))
			st.Utilization = math.Round(st.Utilization*1000) / 1000
		}
		res.Nodes[id] = st
		if n.Type == TypeServer && n.processed > 0 {
			servedByServer = true
		}
		// Busy nearly the whole run means demand exceeded capacity.
		if n.Type == TypeServer && st.Utilization >= 0.95 {
			pct := int(math.Round(st.Utilization * 100))
			msg := fmt.Sprintf("Server overloaded: %d%% CPU utilization. Add a Load Balancer.", pct)
			if hasLB {
				msg = fmt.Sprintf("%s is overloaded: %d%% CPU utilization. Add another server behind the load balancer.", n.name(), pct)
			}
			s.issue(n, "server_overloaded", msg)
		}
	}
	if len(s.issues) == 0 && m.Completed > 0 && !servedByServer {
		s.issue(nil, "no_server", "Requests never reach a Server. Route traffic through an API server.")
	}
	if m.Failed > 0 {
		s.issue(nil, "failed_requests", fmt.Sprintf("%s of %s requests never got a response.", commas(m.Failed), commas(m.Requests)))
	}
	if opts.MaxLatencyMs > 0 && m.Completed > 0 && m.P99Ms > opts.MaxLatencyMs {
		s.issue(nil, "latency", fmt.Sprintf("p99 latency is %.0f ms; the target is %.0f ms or less.", m.P99Ms, opts.MaxLatencyMs))
	}
	res.Cost.Budget = opts.MaxBudget
	if opts.MaxBudget > 0 && res.Cost.Total > opts.MaxBudget {
		s.issue(nil, "over_budget", fmt.Sprintf("This architecture costs $%d/month; the budget is $%d.", res.Cost.Total, opts.MaxBudget))
	}

	keys := make([]string, 0, len(s.issues))
	for k := range s.issues {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	for _, k := range keys {
		res.Issues = append(res.Issues, s.issues[k])
	}
	// Overload is the root cause; show it first.
	slices.SortStableFunc(res.Issues, func(a, b Issue) int {
		return boolInt(b.Code == "server_overloaded") - boolInt(a.Code == "server_overloaded")
	})

	res.Passed = len(res.Issues) == 0 && m.Completed == m.Requests
	if res.Passed {
		res.Message = fmt.Sprintf("Handled %s requests with p99 latency of %.0f ms.", commas(m.Requests), m.P99Ms)
	} else {
		res.Message = res.Issues[0].Message
	}
	res.Timeline = buildTimeline(s, nodes, edges)
	return res
}

func percentile(sorted []float64, p float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	i := int(math.Ceil(p/100*float64(len(sorted)))) - 1
	return round1(sorted[max(0, min(i, len(sorted)-1))])
}

// commas formats n with thousands separators: 1000 → "1,000".
func commas(n int) string {
	s := fmt.Sprint(n)
	for i := len(s) - 3; i > 0 && s[i-1] != '-'; i -= 3 {
		s = s[:i] + "," + s[i:]
	}
	return s
}

func round1(v float64) float64 { return math.Round(v*10) / 10 }

func boolInt(b bool) int {
	if b {
		return 1
	}
	return 0
}
