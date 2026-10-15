// Package simulator runs a discrete-event traffic simulation over a system
// design graph (the React Flow nodes and edges a learner drew) and grades
// the result.
//
// Model: the Client sends a burst of requests at a steady rate. Each request
// follows edges from the client. Load balancers forward round-robin to their
// targets; servers and databases have a fixed number of workers and a FIFO
// queue, so throughput beyond their capacity turns into queueing delay. A
// server calls its downstream node (usually a database) after its own work.
// Every edge adds network latency in each direction.
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
	ID   string `json:"id"`
	Type string `json:"type"`
	Data struct {
		Label string `json:"label"`
	} `json:"data"`
}

type Edge struct {
	ID     string `json:"id"`
	Source string `json:"source"`
	Target string `json:"target"`
}

// Profile is the performance model for one node type.
type Profile struct {
	Workers   int     // concurrent requests in service
	ServiceMs float64 // time to handle one request
}

// Profiles are tuned so one server can't absorb the lesson's burst
// (4 workers / 6 ms ≈ 667 req/s against 1,000 req/s) but two can.
var Profiles = map[string]Profile{
	TypeLoadBalancer: {Workers: 0, ServiceMs: 1}, // 0 = no capacity limit
	TypeServer:       {Workers: 4, ServiceMs: 6},
	TypeDatabase:     {Workers: 50, ServiceMs: 3},
}

// HopMs is the one-way network latency of every edge.
const HopMs = 2

// maxHops stops requests caught in a routing loop.
const maxHops = 32

type Options struct {
	Requests     int     // burst size
	DurationMs   float64 // the burst is spread evenly over this window
	MaxLatencyMs float64 // p99 target; 0 disables the check
}

func (o Options) withDefaults() Options {
	if o.Requests <= 0 {
		o.Requests = 1000
	}
	if o.DurationMs <= 0 {
		o.DurationMs = 1000
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
}

type Result struct {
	Passed  bool                 `json:"passed"`
	Message string               `json:"message"`
	Issues  []Issue              `json:"issues"`
	Metrics Metrics              `json:"metrics"`
	Nodes   map[string]NodeStats `json:"nodes"`
}

// --- simulation state ---

type simNode struct {
	Node
	profile   Profile
	out       []*simNode
	rr        int
	busy      int
	queue     []*request
	busyTime  float64
	processed int
	maxQueue  int
	// Active window, for utilization: first service start to last finish.
	firstStart, lastDone float64
	started              bool
}

func (n *simNode) name() string {
	if n.Data.Label != "" {
		return n.Data.Label
	}
	return n.ID
}

type request struct {
	start   float64
	backMs  float64 // latency of the response's trip back to the client
	hops    int
	visited map[*simNode]bool
}

type eventKind int

const (
	arrive eventKind = iota
	done
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
	failed    int
	issues    map[string]Issue // deduplicated by code+node
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

func (s *sim) fail(t float64) {
	s.failed++
	s.end = max(s.end, t)
}

func (s *sim) complete(t float64, req *request) {
	finish := t + req.backMs
	s.latencies = append(s.latencies, finish-req.start)
	s.end = max(s.end, finish)
}

// forward sends req from one node to the next over an edge.
func (s *sim) forward(t float64, req *request, from, to *simNode) {
	req.hops++
	if req.hops > maxHops {
		s.issue(from, "routing_loop", fmt.Sprintf("Requests loop forever through %s. Remove the cycle.", from.name()))
		s.fail(t)
		return
	}
	req.backMs += HopMs
	s.schedule(t+HopMs, arrive, req, to)
}

// next picks a downstream node, round-robin.
func (n *simNode) next() *simNode {
	if len(n.out) == 0 {
		return nil
	}
	target := n.out[n.rr%len(n.out)]
	n.rr++
	return target
}

func (s *sim) handle(e *event) {
	n, req := e.node, e.req
	switch e.kind {
	case arrive:
		switch n.Type {
		case TypeLoadBalancer:
			n.processed++
			target := n.next()
			if target == nil {
				s.issue(n, "dead_end", fmt.Sprintf("%s isn't connected to any servers.", n.name()))
				s.fail(e.t)
				return
			}
			s.forward(e.t+n.profile.ServiceMs, req, n, target)
		case TypeClient:
			s.issue(n, "loop_to_client", "Requests are routed back into a Client. Edges should point away from the client.")
			s.fail(e.t)
		default:
			if n.busy < n.profile.Workers {
				s.startService(e.t, req, n)
			} else {
				n.queue = append(n.queue, req)
				n.maxQueue = max(n.maxQueue, len(n.queue))
			}
		}
	case done:
		n.busy--
		n.processed++
		n.lastDone = e.t
		if len(n.queue) > 0 {
			queued := n.queue[0]
			n.queue = n.queue[1:]
			s.startService(e.t, queued, n)
		}
		// Servers call their downstream (usually a database); a node only
		// handles a given request once, so A→B→A doesn't loop.
		if target := n.next(); target != nil && n.Type == TypeServer && !req.visited[target] {
			s.forward(e.t, req, n, target)
			return
		}
		s.complete(e.t, req)
	}
}

func (s *sim) startService(t float64, req *request, n *simNode) {
	if !n.started {
		n.started, n.firstStart = true, t
	}
	n.busy++
	n.busyTime += n.profile.ServiceMs
	req.visited[n] = true
	s.schedule(t+n.profile.ServiceMs, done, req, n)
}

// Run simulates the burst over g and grades it. It returns an error only for
// malformed input; design mistakes are reported as Issues.
func Run(g Graph, opts Options) (Result, error) {
	opts = opts.withDefaults()
	nodes := map[string]*simNode{}
	var clients []*simNode
	for _, n := range g.Nodes {
		if n.ID == "" {
			return Result{}, fmt.Errorf("node without an id")
		}
		if _, dup := nodes[n.ID]; dup {
			return Result{}, fmt.Errorf("duplicate node id %q", n.ID)
		}
		sn := &simNode{Node: n}
		switch n.Type {
		case TypeClient:
			clients = append(clients, sn)
		case TypeLoadBalancer, TypeServer, TypeDatabase:
			sn.profile = Profiles[n.Type]
		default:
			return Result{}, fmt.Errorf("unknown node type %q", n.Type)
		}
		nodes[n.ID] = sn
	}
	for _, e := range g.Edges {
		from, to := nodes[e.Source], nodes[e.Target]
		if from == nil || to == nil {
			return Result{}, fmt.Errorf("edge %q connects a node that doesn't exist", e.ID)
		}
		if from != to && !slices.Contains(from.out, to) {
			from.out = append(from.out, to)
		}
	}

	s := &sim{issues: map[string]Issue{}}
	res := Result{Issues: []Issue{}, Nodes: map[string]NodeStats{}, Metrics: Metrics{Requests: opts.Requests, MaxLatencyMs: opts.MaxLatencyMs}}

	switch {
	case len(clients) == 0:
		s.issue(nil, "no_client", "Add a Client node to send traffic.")
	case len(clients) > 1:
		s.issue(nil, "multiple_clients", "Use a single Client node; it represents all of your users.")
	case len(clients[0].out) == 0:
		s.issue(clients[0], "client_disconnected", "Connect the Client to the rest of your system.")
	}
	if len(s.issues) > 0 {
		return finish(res, s, nodes, opts), nil
	}

	client := clients[0]
	interval := opts.DurationMs / float64(opts.Requests)
	for i := range opts.Requests {
		t := float64(i) * interval
		req := &request{start: t, visited: map[*simNode]bool{}}
		s.forward(t, req, client, client.next())
	}
	for s.events.Len() > 0 {
		s.handle(heap.Pop(&s.events).(*event))
	}
	return finish(res, s, nodes, opts), nil
}

// finish computes metrics and grades the run.
func finish(res Result, s *sim, nodes map[string]*simNode, opts Options) Result {
	m := &res.Metrics
	m.Completed, m.Failed = len(s.latencies), s.failed
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
		if window := n.lastDone - n.firstStart; n.profile.Workers > 0 && window > 0 {
			st.Utilization = math.Min(1, n.busyTime/(float64(n.profile.Workers)*window))
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
