// Package simulator runs a discrete-event traffic simulation over a system
// design graph (the React Flow nodes and edges a learner drew) and grades
// the result.
//
// Model: the Client sends requests at a steady rate, plus any spikes the
// lesson's scenario adds. Requests are reads, writes, or static assets, and
// reads and writes touch records (keys) with a skewed popularity. Each
// request follows edges from the client:
//
//   - CDNs serve static assets they've cached and pass everything else on.
//   - Rate limiters allow each user a number of requests per second.
//   - Load balancers spread requests across healthy targets.
//   - Servers do some work, then send reads and writes on to the closest
//     store: a cache, then a read replica, then a database (writes prefer
//     a message queue, and skip replicas).
//   - Caches answer reads they hold and fill on misses; writes pass
//     through, and the "invalidate" policy drops the cached copy.
//   - Databases commit writes (optionally publishing each change to
//     connected queues: change data capture). Read replicas trail their
//     primary by ReplicaLagMs, so reads there can be stale.
//   - Message queues acknowledge writes immediately and deliver every
//     message to each downstream subscriber, retrying until it succeeds.
//   - Servers connected straight to a search index also write to it after
//     the database commits (a "dual write" that is lost if it fails).
//
// Servers, caches, databases, replicas, and search indexes have a pool of
// workers and a FIFO queue, so demand beyond their capacity turns into
// queueing delay. Every edge adds network latency in each direction.
//
// Faults (from the scenario) and chaos experiments crash nodes or cut
// edges. A rolling deployment upgrades servers one at a time, and a schema
// registry decides whether each app version can read the other's messages.
//
// Besides the summary, Run records a timeline of frames (per-node load and
// per-edge traffic) and notable events, for replaying the run.
package simulator

import (
	"container/heap"
	"fmt"
	"math"
	"slices"
	"strings"
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
	// Server: connection pool (requests served at once) and the app
	// version it runs.
	Pool    int    `json:"pool,omitempty"`
	Version string `json:"version,omitempty"`
	// Database: standby replica mode ("none", "sync", "async"), number of
	// partitions, whether it publishes changes (outbox / change data
	// capture), and whether it rejects writes with stale fencing tokens.
	Replication string `json:"replication,omitempty"`
	Partitions  int    `json:"partitions,omitempty"`
	Outbox      bool   `json:"outbox,omitempty"`
	CheckTokens bool   `json:"checkTokens,omitempty"`
	// Load balancer: "round_robin" or "least_connections".
	Algorithm string `json:"algorithm,omitempty"`
	// Cache: "ttl" (entries expire) or "invalidate" (writes drop them).
	Policy string `json:"policy,omitempty"`
	TTLMs  int    `json:"ttlMs,omitempty"`
	// Rate limiter: requests per second allowed per user.
	Limit int `json:"limit,omitempty"`
	// Message queue: deliveries in flight to each subscriber.
	Consumers int `json:"consumers,omitempty"`
	// Lock service: lease length, and whether it issues fencing tokens.
	LeaseMs int  `json:"leaseMs,omitempty"`
	Fencing bool `json:"fencing,omitempty"`
	// Schema registry: the new (v2) message schema.
	Fields []Field `json:"fields,omitempty"`
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
	FailoverMs    = 150 // a standby takes over from a crashed database
	TimeoutMs     = 100 // a request over a cut edge gives up
	ReplicaLagMs  = 50  // async replicas trail the primary by this much
	SyncReplicaMs = 4   // sync replication waits for the replica's ack
	RetryMs       = 50  // a queue retries a failed delivery after this
	retryHorizon  = 5000
	maxHops       = 32 // stops requests caught in a routing loop
	maxEvents     = 60
)

type Options struct {
	Requests     int     // overrides the scenario's request count
	DurationMs   float64 // overrides the scenario's duration
	MaxLatencyMs float64 // p99 target; 0 disables the check
	MaxBudget    int     // monthly cost limit; 0 disables the check
	Chaos        Chaos
	Scenario     Scenario
}

func (o Options) withDefaults() Options {
	if o.Requests > 0 {
		o.Scenario.Traffic.Requests = o.Requests
	}
	if o.DurationMs > 0 {
		o.Scenario.Traffic.DurationMs = o.DurationMs
	}
	o.Scenario = o.Scenario.withDefaults()
	o.Requests, o.DurationMs = o.Scenario.Traffic.Requests, o.Scenario.Traffic.DurationMs
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
	Utilization float64 `json:"utilization"` // 0..1, busiest partition's worker time
	MaxQueue    int     `json:"maxQueue"`
	Pool        int     `json:"pool,omitempty"`
}

// Stat is a scenario-specific measurement shown with the results.
type Stat struct {
	Label  string `json:"label"`
	Value  string `json:"value"`
	Status string `json:"status,omitempty"` // "good", "bad", or ""
}

type Result struct {
	Passed   bool                 `json:"passed"`
	Message  string               `json:"message"`
	Issues   []Issue              `json:"issues"`
	Metrics  Metrics              `json:"metrics"`
	Stats    []Stat               `json:"stats"`
	Nodes    map[string]NodeStats `json:"nodes"`
	Cost     CostBreakdown        `json:"cost"`
	Timeline Timeline             `json:"timeline"`
	// Experiment is set for chaos runs, which don't count as lesson attempts.
	Experiment bool `json:"experiment,omitempty"`
}

// --- simulation state ---

type simEdge struct {
	id       string
	from, to *simNode
	cuts     [][2]float64
	requests []float64
}

func (e *simEdge) isCut(t float64) bool { return within(e.cuts, t) }

// shard is a pool of workers with its own queue; partitioned databases
// have several.
type shard struct {
	workers   int
	busy      int
	queue     []*request
	inService []*request
	maxQueue  int
	// Active window, for utilization: first service start to last finish.
	firstStart, lastDone float64
	started              bool
	busySpans            [][2]float64
	queueLog             [][2]float64 // (time, queue length) after each change
}

type cacheEntry struct {
	version int
	expires float64
}

type bucket struct {
	tokens, last float64
}

type message struct {
	key, version int
	write        bool    // a buffered write (vs. a change event)
	at           float64 // when it was published
}

type subscriber struct {
	edge      *simEdge
	cursor    int   // next message to deliver
	retry     []int // messages to redeliver
	inflight  int
	delivered int
	pumping   bool // a retry is scheduled
}

type simNode struct {
	Node
	spec      NodeSpec
	serviceMs float64
	out       []*simEdge
	in        []*simEdge
	rr        int
	shards    []*shard
	processed int
	downs     [][2]float64
	drains    [][2]float64 // rolling deploy: out of rotation
	upgradeAt float64
	upgradeTo string
	writes    []float64 // database: commit times, for async data loss
	// Cache and CDN contents.
	entries     map[int]cacheEntry
	ttl         float64
	hits, reads int
	// Rate limiter.
	buckets map[int]*bucket
	limit   float64
	// Message queue.
	topic     []message
	subs      []*subscriber
	backlog   [][2]float64
	consumers int
	// Search index.
	indexed map[int]int
	// Stale reads served here.
	stale int
}

func (n *simNode) name() string {
	if n.Data.Label != "" {
		return n.Data.Label
	}
	return n.ID
}

func (n *simNode) isDown(t float64) bool     { return within(n.downs, t) }
func (n *simNode) isDraining(t float64) bool { return within(n.drains, t) }

func (n *simNode) version(t float64) string {
	if n.upgradeTo != "" && t >= n.upgradeAt {
		return n.upgradeTo
	}
	if n.Data.Version != "" {
		return n.Data.Version
	}
	return "v1"
}

func within(spans [][2]float64, t float64) bool {
	for _, s := range spans {
		if t >= s[0] && t < s[1] {
			return true
		}
	}
	return false
}

func (n *simNode) shardFor(req *request) (int, *shard) {
	i := 0
	if len(n.shards) > 1 {
		i = req.key % len(n.shards)
	}
	return i, n.shards[i]
}

// task is internal work: a queue delivery or a dual write.
type task struct {
	kind  string // "deliver" or "index"
	queue *simNode
	sub   *subscriber
	msg   int
	key   int
	ver   int
}

type request struct {
	start   float64
	backMs  float64 // latency of the response's trip back to the client
	hops    int
	visited map[*simNode]bool
	failed  bool
	class   string
	key     int
	user    int
	version string     // client app version
	caches  []*simNode // caches passed on the way, to fill or invalidate
	cdns    []*simNode // CDNs that missed, to fill
	server  *simNode   // the last server, for its dual writes
	task    *task
}

type eventKind int

const (
	arrive eventKind = iota
	done
	crash
	recover
	fill
	invalidate
	ack
	pump
)

type event struct {
	t     float64
	seq   int
	kind  eventKind
	req   *request
	node  *simNode
	shard int
	key   int
	ver   int
	sub   *subscriber
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
	horizon   float64 // queues stop retrying after this
	// Data: commit times per record, in order.
	commits   map[int][]float64
	hasData   bool // the traffic includes writes
	schemas   map[string][]Field
	reads     int
	stale     int
	botSent   int
	botBlock  int
	userBlock int
	lostDual  int
	writeCost float64
	writeLat  []float64 // write requests' latency
	lags      []float64 // queued writes: publish to first delivery
}

func (s *sim) schedule(e *event) {
	s.seq++
	e.seq = s.seq
	heap.Push(&s.events, e)
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
	if req.task != nil {
		s.taskFailed(t, req, n, why)
		return
	}
	if req.user == botUser {
		return
	}
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
	if req.task != nil {
		s.taskDone(t, req)
		return
	}
	finish := t + req.backMs
	if req.user == botUser {
		return
	}
	if req.class == ClassWrite {
		s.writeLat = append(s.writeLat, finish-req.start)
	}
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
	if e.isCut(t) {
		s.fail(t+TimeoutMs, req, from, fmt.Sprintf("Requests from %s to %s time out: the connection is cut", from.name(), e.to.name()))
		return
	}
	req.backMs += HopMs
	s.schedule(&event{t: t + HopMs, kind: arrive, req: req, node: e.to})
}

// accepts reports whether a node of type typ can handle a request class.
func accepts(typ, class string) bool {
	switch typ {
	case TypeLock, TypeSchemaRegistry, TypeSearchIndex:
		return false
	case TypeReplica:
		return class == ClassRead
	case TypeQueue:
		return class == ClassWrite
	case TypeCache, TypeDatabase:
		return class != ClassStatic
	}
	return true
}

// rank orders where a server sends each class: reads go to the closest
// store (cache, then replica, then database), writes prefer a queue.
func rank(typ, class string) int {
	order := map[string][]string{
		ClassRead:  {TypeCache, TypeReplica, TypeDatabase},
		ClassWrite: {TypeQueue, TypeCache, TypeDatabase},
	}[class]
	if i := slices.Index(order, typ); i >= 0 {
		return i
	}
	return len(order)
}

// healthy reports whether a load balancer still sends to edge e at time t:
// it stops once health checks have noticed the target or link is down, and
// immediately for a server drained for a deploy.
func healthy(e *simEdge, t float64) bool {
	return !e.isCut(t-DetectMs) && !e.to.isDown(t-DetectMs) && !e.to.isDraining(t)
}

// route picks the next edge for req, or nil.
func (n *simNode) route(t float64, req *request) *simEdge {
	var candidates []*simEdge
	best := math.MaxInt
	for _, e := range n.out {
		if !accepts(e.to.Type, req.class) || req.visited[e.to] {
			continue
		}
		if n.Type == TypeLoadBalancer && !healthy(e, t) {
			continue
		}
		r := 0
		if n.Type == TypeServer || n.Type == TypeCache {
			r = rank(e.to.Type, req.class)
		}
		if r < best {
			best, candidates = r, nil
		}
		if r == best {
			candidates = append(candidates, e)
		}
	}
	if len(candidates) == 0 {
		return nil
	}
	pick := candidates[n.rr%len(candidates)]
	n.rr++
	if n.Type == TypeLoadBalancer && n.Data.Algorithm == "least_connections" {
		for _, e := range candidates {
			if load(e.to) < load(pick.to) {
				pick = e
			}
		}
	}
	return pick
}

func load(n *simNode) int {
	total := 0
	for _, sh := range n.shards {
		total += sh.busy + len(sh.queue)
	}
	return total
}

func (s *sim) handle(e *event) {
	n, req := e.node, e.req
	switch e.kind {
	case crash:
		s.crash(e.t, n)
	case recover:
		msg := fmt.Sprintf("%s is back up", n.name())
		if n.Type == TypeDatabase && n.Data.Replication != "" && n.Data.Replication != "none" {
			msg = fmt.Sprintf("%s's standby took over", n.name())
		}
		s.log = append(s.log, Event{T: round1(e.t), Kind: "failover", NodeID: n.ID, Message: msg})
	case fill:
		if !n.isDown(e.t) {
			n.entries[e.key] = cacheEntry{version: e.ver, expires: e.t + n.ttl}
		}
	case invalidate:
		if !n.isDown(e.t) {
			delete(n.entries, e.key)
		}
	case ack:
		e.sub.inflight--
		e.sub.delivered++
		s.pump(e.t, n, e.sub)
	case pump:
		e.sub.pumping = false
		s.pump(e.t, n, e.sub)
	case arrive:
		s.arrive(e.t, n, req)
	case done:
		sh := n.shards[e.shard]
		if !slices.Contains(sh.inService, req) {
			return // lost in a crash
		}
		sh.inService = slices.DeleteFunc(sh.inService, func(r *request) bool { return r == req })
		sh.busy--
		n.processed++
		sh.lastDone = e.t
		if len(sh.queue) > 0 {
			queued := sh.queue[0]
			sh.queue = sh.queue[1:]
			sh.queueLog = append(sh.queueLog, [2]float64{e.t, float64(len(sh.queue))})
			s.startService(e.t, queued, n, e.shard)
		}
		s.served(e.t, n, req)
	}
}

func (s *sim) arrive(t float64, n *simNode, req *request) {
	if req.failed {
		return
	}
	if n.isDown(t) {
		s.fail(t, req, n, fmt.Sprintf("%s is down: requests to it fail", n.name()))
		return
	}
	switch n.Type {
	case TypeClient:
		s.issue(n, "loop_to_client", "Requests are routed back into a Client. Edges should point away from the client.")
		s.fail(t, req, n, "Requests are routed back into the Client")
	case TypeLoadBalancer, TypeRateLimiter, TypeCDN:
		n.processed++
		at := t + n.serviceMs
		if n.Type == TypeRateLimiter && !s.allow(t, n, req) {
			return
		}
		if n.Type == TypeCDN && req.class == ClassStatic {
			n.reads++
			if _, ok := n.entries[req.key]; ok {
				n.hits++
				s.complete(at, req)
				return
			}
			req.cdns = append(req.cdns, n)
		}
		target := n.route(t, req)
		if target == nil {
			switch {
			case len(n.out) == 0 && n.Type == TypeLoadBalancer:
				s.issue(n, "dead_end", fmt.Sprintf("%s isn't connected to any servers.", n.name()))
			case len(n.out) == 0:
				s.issue(n, "dead_end", fmt.Sprintf("%s isn't connected to anything behind it.", n.name()))
			case n.Type == TypeLoadBalancer:
				s.issue(n, "no_healthy_targets", fmt.Sprintf("%s has no healthy servers left to send traffic to.", n.name()))
			}
			s.fail(t, req, n, fmt.Sprintf("%s has nowhere to send requests", n.name()))
			return
		}
		s.forward(at, req, n, target)
	case TypeQueue:
		n.processed++
		at := t + n.serviceMs
		if req.task != nil && req.task.kind == "deliver" {
			// A queue feeding a queue: re-publish.
			m := req.task.queue.topic[req.task.msg]
			s.publish(at, n, m)
			s.complete(at, req)
			return
		}
		s.publish(at, n, message{key: req.key, write: true, at: at})
		s.complete(at, req) // acknowledged once it's durably queued
	case TypeServer:
		if s.schemas != nil && req.version != "" && req.task == nil {
			sv := n.version(t)
			if msg := decode(s.schemas[req.version], s.schemas[sv], req.version, sv); msg != "" {
				s.issue(nil, "schema_"+req.version+"_"+sv, msg)
				s.fail(t, req, n, fmt.Sprintf("%s (%s) rejected a %s request", n.name(), sv, req.version))
				return
			}
		}
		s.enqueue(t, n, req)
	case TypeCache, TypeDatabase, TypeReplica, TypeSearchIndex:
		s.enqueue(t, n, req)
	default:
		s.fail(t, req, n, fmt.Sprintf("%s can't handle requests", n.name()))
	}
}

// allow applies a rate limiter's per-user token bucket.
func (s *sim) allow(t float64, n *simNode, req *request) bool {
	if req.task != nil {
		return true
	}
	b := n.buckets[req.user]
	if b == nil {
		b = &bucket{tokens: n.limit, last: t}
		n.buckets[req.user] = b
	}
	b.tokens = math.Min(n.limit, b.tokens+(t-b.last)*n.limit/1000)
	b.last = t
	if b.tokens >= 1 {
		b.tokens--
		return true
	}
	if req.user == botUser {
		s.botBlock++
		s.event(t, "throttled", n.ID, "", fmt.Sprintf("%s started rejecting the bot's requests", n.name()))
		req.failed = true
		return false
	}
	s.userBlock++
	s.fail(t, req, n, fmt.Sprintf("%s rejected requests from real users", n.name()))
	return false
}

func (s *sim) enqueue(t float64, n *simNode, req *request) {
	i, sh := n.shardFor(req)
	if sh.busy < sh.workers {
		s.startService(t, req, n, i)
		return
	}
	sh.queue = append(sh.queue, req)
	sh.maxQueue = max(sh.maxQueue, len(sh.queue))
	sh.queueLog = append(sh.queueLog, [2]float64{t, float64(len(sh.queue))})
	if len(sh.queue) == 10 {
		s.event(t, "queueing", n.ID, "", fmt.Sprintf("Requests started piling up at %s", n.name()))
	}
}

func (s *sim) startService(t float64, req *request, n *simNode, i int) {
	sh := n.shards[i]
	if !sh.started {
		sh.started, sh.firstStart = true, t
	}
	sh.busy++
	took := n.serviceMs
	if n.Type == TypeDatabase && req.class == ClassWrite {
		// Fan-out multiplies the database's own work, not the wait
		// for a sync standby's acknowledgment.
		took = n.spec.ServiceMs*s.writeCost + (n.serviceMs - n.spec.ServiceMs)
	}
	sh.busySpans = append(sh.busySpans, [2]float64{t, t + took})
	sh.inService = append(sh.inService, req)
	req.visited[n] = true
	s.schedule(&event{t: t + took, kind: done, req: req, node: n, shard: i})
}

// served continues a request after a node finishes its work on it.
func (s *sim) served(t float64, n *simNode, req *request) {
	if req.failed {
		return
	}
	if tk := req.task; tk != nil && n.Type != TypeServer {
		s.applyTask(t, n, req)
		return
	}
	switch n.Type {
	case TypeServer:
		if s.schemas != nil && req.version != "" && req.task == nil {
			sv := n.version(t)
			if msg := decode(s.schemas[sv], s.schemas[req.version], sv, req.version); msg != "" {
				s.issue(nil, "schema_"+sv+"_"+req.version, msg)
				s.fail(t, req, n, fmt.Sprintf("%s clients couldn't read responses from %s (%s)", req.version, n.name(), sv))
				return
			}
		}
		if req.class == ClassStatic {
			s.fillCDNs(t, req)
			s.complete(t, req)
			return
		}
		req.server = n
		if target := n.route(t, req); target != nil {
			s.forward(t, req, n, target)
			return
		}
		if s.hasData {
			s.issue(n, "no_storage", fmt.Sprintf("%s has nowhere to read or write data. Connect it to a database.", n.name()))
			s.fail(t, req, n, fmt.Sprintf("%s has no database", n.name()))
			return
		}
		s.complete(t, req)
	case TypeCache:
		if req.class == ClassRead {
			n.reads++
			if en, ok := n.entries[req.key]; ok && t < en.expires {
				n.hits++
				s.finishRead(t, req, en.version, n)
				return
			}
		}
		req.caches = append(req.caches, n)
		target := n.route(t, req)
		if target == nil {
			s.issue(n, "cache_dead_end", fmt.Sprintf("%s has no database behind it to load data from.", n.name()))
			s.fail(t, req, n, fmt.Sprintf("%s has no database behind it", n.name()))
			return
		}
		s.forward(t, req, n, target)
	case TypeDatabase:
		if req.class == ClassWrite {
			s.commit(t, n, req.key, req)
			s.complete(t, req)
			return
		}
		s.finishRead(t, req, s.versionAt(req.key, t), n)
	case TypeReplica:
		s.finishRead(t, req, s.replicaVersion(n, req.key, t), n)
	default:
		s.complete(t, req)
	}
}

// versionAt is how many writes to key have committed by time t.
func (s *sim) versionAt(key int, t float64) int {
	c := s.commits[key]
	i, _ := slices.BinarySearch(c, math.Nextafter(t, math.Inf(1)))
	return i
}

// replicaVersion is what a read replica holds: its primary as of
// ReplicaLagMs ago, frozen while the replication link is cut.
func (s *sim) replicaVersion(n *simNode, key int, t float64) int {
	var src *simEdge
	for _, e := range n.in {
		if e.from.Type == TypeDatabase {
			src = e
			break
		}
	}
	if src == nil {
		s.issue(n, "replica_without_primary", fmt.Sprintf("%s isn't connected to a primary database, so it never receives any data. Draw an edge from the database to it.", n.name()))
		return 0
	}
	at := t - ReplicaLagMs
	for _, c := range src.cuts {
		if at >= c[0] && at < c[1] {
			at = c[0]
		}
	}
	return s.versionAt(key, at)
}

func (s *sim) finishRead(t float64, req *request, version int, at *simNode) {
	for _, c := range req.caches {
		s.schedule(&event{t: t + HopMs, kind: fill, node: c, key: req.key, ver: version})
	}
	if req.user != botUser {
		s.reads++
		if version < s.versionAt(req.key, req.start) {
			s.stale++
			at.stale++
			s.event(t, "stale", at.ID, "", fmt.Sprintf("Users read outdated data from %s", at.name()))
		}
	}
	s.complete(t, req)
}

func (s *sim) fillCDNs(t float64, req *request) {
	for _, c := range req.cdns {
		c.entries[req.key] = cacheEntry{expires: math.Inf(1)}
	}
}

// commit records a write at database n, then replicates and publishes it.
func (s *sim) commit(t float64, n *simNode, key int, req *request) {
	s.commits[key] = append(s.commits[key], t)
	ver := len(s.commits[key])
	n.writes = append(n.writes, t)
	for _, e := range n.out {
		if e.to.Type != TypeQueue {
			continue
		}
		if !n.Data.Outbox {
			s.issue(n, "no_outbox", fmt.Sprintf("%s doesn't publish its changes. Turn on change data capture (the outbox) so it sends each committed write to %s.", n.name(), e.to.name()))
			continue
		}
		e.requests = append(e.requests, t)
		if !e.isCut(t) && !e.to.isDown(t+HopMs) {
			s.publish(t+HopMs, e.to, message{key: key, version: ver})
		}
	}
	if req == nil {
		return
	}
	for _, c := range req.caches {
		if c.Data.Policy == "invalidate" {
			s.schedule(&event{t: t + HopMs, kind: invalidate, node: c, key: key})
		}
	}
	// Dual writes: the server writes to search indexes it's connected to.
	if srv := req.server; srv != nil && req.task == nil {
		for _, e := range srv.out {
			if e.to.Type != TypeSearchIndex {
				continue
			}
			sent := t + HopMs // the commit's ack reaches the server
			idx := &request{start: sent, visited: map[*simNode]bool{}, key: key, task: &task{kind: "index", key: key, ver: ver}}
			s.forward(sent, idx, srv, e)
		}
	}
}

// publish appends a message to a queue and starts delivering it.
func (s *sim) publish(t float64, q *simNode, m message) {
	q.topic = append(q.topic, m)
	if len(q.subs) == 0 && len(q.topic) == 1 {
		s.issue(q, "queue_no_subscribers", fmt.Sprintf("Nothing reads from %s. Connect it to the services that should receive its messages.", q.name()))
	}
	for _, sub := range q.subs {
		s.pump(t, q, sub)
	}
	s.logBacklog(t, q)
}

// pump sends queued messages to a subscriber, up to the queue's consumer
// limit.
func (s *sim) pump(t float64, q *simNode, sub *subscriber) {
	for sub.inflight < q.consumers {
		var msg int
		switch {
		case len(sub.retry) > 0:
			msg, sub.retry = sub.retry[0], sub.retry[1:]
		case sub.cursor < len(q.topic):
			msg = sub.cursor
			sub.cursor++
			if m := q.topic[msg]; m.write {
				s.lags = append(s.lags, t-m.at)
			}
		default:
			s.logBacklog(t, q)
			return
		}
		sub.inflight++
		m := q.topic[msg]
		class := ClassWrite
		if !m.write {
			class = "event"
		}
		req := &request{start: t, visited: map[*simNode]bool{}, key: m.key, class: class,
			task: &task{kind: "deliver", queue: q, sub: sub, msg: msg, key: m.key, ver: m.version}}
		s.forward(t+q.serviceMs, req, q, sub.edge)
	}
	s.logBacklog(t, q)
}

func (s *sim) logBacklog(t float64, q *simNode) {
	pending := 0
	for _, sub := range q.subs {
		pending = max(pending, len(q.topic)-sub.cursor+len(sub.retry)+sub.inflight)
	}
	if l := len(q.backlog); l > 0 && q.backlog[l-1][1] == float64(pending) {
		return
	}
	q.backlog = append(q.backlog, [2]float64{t, float64(pending)})
	if pending >= 100 {
		s.event(t, "queueing", q.ID, "", fmt.Sprintf("%s's backlog passed 100 messages", q.name()))
	}
}

// applyTask finishes internal work at its destination.
func (s *sim) applyTask(t float64, n *simNode, req *request) {
	tk := req.task
	switch n.Type {
	case TypeDatabase:
		if req.class == ClassWrite {
			s.commit(t, n, tk.key, nil)
		}
	case TypeCache:
		delete(n.entries, tk.key)
	case TypeSearchIndex:
		if tk.ver > n.indexed[tk.key] {
			n.indexed[tk.key] = tk.ver
		}
	}
	s.complete(t, req)
}

func (s *sim) taskDone(t float64, req *request) {
	s.end = max(s.end, t)
	if tk := req.task; tk.kind == "deliver" {
		s.schedule(&event{t: t + HopMs, kind: ack, node: tk.queue, sub: tk.sub})
	}
}

func (s *sim) taskFailed(t float64, req *request, n *simNode, why string) {
	tk := req.task
	if tk.kind == "index" {
		s.lostDual++
		id := ""
		if n != nil {
			id = n.ID
		}
		s.event(t, "data_loss", id, "", "A dual write to the search index was lost: "+why)
		return
	}
	// Queues keep the message and retry the delivery.
	tk.sub.inflight--
	tk.sub.retry = append(tk.sub.retry, tk.msg)
	if !tk.sub.pumping && t < s.horizon {
		tk.sub.pumping = true
		s.schedule(&event{t: t + RetryMs, kind: pump, node: tk.queue, sub: tk.sub})
	}
	s.logBacklog(t, tk.queue)
}

// crash takes a node down: everything in flight or queued there fails, and
// in-memory state (caches) is lost.
func (s *sim) crash(t float64, n *simNode) {
	for _, sh := range n.shards {
		for _, r := range append(sh.inService, sh.queue...) {
			s.fail(t, r, n, fmt.Sprintf("Work in progress on %s was lost", n.name()))
		}
		sh.inService, sh.queue, sh.busy = nil, nil, 0
		sh.queueLog = append(sh.queueLog, [2]float64{t, 0})
		for i, span := range sh.busySpans {
			if span[1] > t {
				sh.busySpans[i][1] = max(span[0], t)
			}
		}
	}
	if n.Type == TypeCache {
		clear(n.entries)
	}
	if n.Type == TypeDatabase && n.Data.Replication == "async" {
		lost := 0
		for _, w := range n.writes {
			if w > t-ReplicaLagMs {
				lost++
			}
		}
		if lost > 0 {
			s.issue(n, "data_loss", fmt.Sprintf("%d writes %s had confirmed were lost: async replication hadn't copied them to the standby yet.", lost, n.name()))
			s.event(t, "data_loss", n.ID, "", fmt.Sprintf("%d confirmed writes lost in failover", lost))
		}
	}
}

// Run simulates the scenario over g and grades it. It returns an error only
// for malformed input; design mistakes are reported as Issues.
func Run(g Graph, opts Options) (Result, error) {
	opts = opts.withDefaults()
	if err := opts.Scenario.Validate(); err != nil {
		return Result{}, err
	}
	cost, err := Cost(g)
	if err != nil {
		return Result{}, err
	}
	if opts.Scenario.Kind == "fencing" {
		return runFencing(g, opts, cost)
	}
	nodes, edges, err := build(g)
	if err != nil {
		return Result{}, err
	}
	sc := opts.Scenario
	s := &sim{issues: map[string]Issue{}, logged: map[string]bool{}, commits: map[int][]float64{},
		hasData: sc.Traffic.Mix[ClassWrite] > 0, horizon: opts.DurationMs + retryHorizon, writeCost: float64(max(1, sc.Traffic.WriteCost))}
	res := Result{Issues: []Issue{}, Stats: []Stat{}, Nodes: map[string]NodeStats{}, Cost: cost, Experiment: !opts.Chaos.Empty(),
		Metrics: Metrics{MaxLatencyMs: opts.MaxLatencyMs}}

	if err := s.applyChaos(opts.Chaos, nodes, edges); err != nil {
		return Result{}, err
	}
	s.applyFaults(sc.Faults, nodes, edges)
	s.applyRollout(sc.Rollout, nodes)
	if err := s.loadSchemas(sc, nodes); err != nil {
		return Result{}, err
	}

	var clients []*simNode
	for _, n := range sortedNodes(nodes) {
		if n.Type == TypeClient {
			clients = append(clients, n)
		}
	}
	switch {
	case len(clients) == 0:
		s.issue(nil, "no_client", "Add a Client node to send traffic.")
	case len(clients) > 1:
		s.issue(nil, "multiple_clients", "Use a single Client node; it represents all of your users.")
	case len(clients[0].out) == 0:
		s.issue(clients[0], "client_disconnected", "Connect the Client to the rest of your system.")
	}
	for _, typ := range sc.Goals.Require {
		if !slices.ContainsFunc(g.Nodes, func(n Node) bool { return n.Type == typ }) {
			s.issue(nil, "missing_"+typ, fmt.Sprintf("This design needs a %s.", catalog[typ].Name))
		}
	}
	if len(s.issues) > 0 {
		return finish(res, s, nodes, edges, opts), nil
	}

	client := clients[0]
	for _, a := range sc.Traffic.arrivals() {
		req := &request{start: a.t, visited: map[*simNode]bool{}, class: a.class, key: a.key, user: a.user, version: a.version}
		if a.user == botUser {
			s.botSent++
		} else {
			res.Metrics.Requests++
		}
		target := client.route(a.t, req)
		if target == nil {
			s.issue(client, "client_dead_end", fmt.Sprintf("Nothing connected to the Client can handle %s requests.", a.class))
			s.fail(a.t, req, client, "The Client has nowhere to send requests")
			continue
		}
		s.forward(a.t, req, client, target)
	}
	for s.events.Len() > 0 {
		s.handle(heap.Pop(&s.events).(*event))
	}
	return finish(res, s, nodes, edges, opts), nil
}

func build(g Graph) (map[string]*simNode, map[string]*simEdge, error) {
	nodes := map[string]*simNode{}
	for _, n := range g.Nodes {
		if n.ID == "" {
			return nil, nil, fmt.Errorf("node without an id")
		}
		if _, dup := nodes[n.ID]; dup {
			return nil, nil, fmt.Errorf("duplicate node id %q", n.ID)
		}
		spec := catalog[n.Type] // Cost validated the type and settings
		sn := &simNode{Node: n, spec: spec, serviceMs: spec.ServiceMs, entries: map[int]cacheEntry{},
			buckets: map[int]*bucket{}, indexed: map[int]int{}}
		workers, parts := spec.Workers, 1
		switch n.Type {
		case TypeServer:
			if n.Data.Pool > 0 {
				workers = n.Data.Pool
			}
		case TypeDatabase:
			if n.Data.Replication == "sync" {
				sn.serviceMs += SyncReplicaMs
			}
			parts = max(1, n.Data.Partitions)
		case TypeCache:
			sn.ttl = float64(spec.DefaultTTLMs)
			if n.Data.TTLMs > 0 {
				sn.ttl = float64(n.Data.TTLMs)
			}
		case TypeRateLimiter:
			sn.limit = float64(spec.DefaultLimit)
			if n.Data.Limit > 0 {
				sn.limit = float64(n.Data.Limit)
			}
		case TypeQueue:
			sn.consumers = spec.DefaultConsumers
			if n.Data.Consumers > 0 {
				sn.consumers = n.Data.Consumers
			}
		}
		if workers > 0 {
			for range parts {
				sn.shards = append(sn.shards, &shard{workers: workers})
			}
		}
		nodes[n.ID] = sn
	}
	edges := map[string]*simEdge{}
	for i, e := range g.Edges {
		from, to := nodes[e.Source], nodes[e.Target]
		if from == nil || to == nil {
			return nil, nil, fmt.Errorf("edge %q connects a node that doesn't exist", e.ID)
		}
		id := e.ID
		if id == "" {
			id = fmt.Sprintf("edge-%d", i)
		}
		if from != to && !slices.ContainsFunc(from.out, func(x *simEdge) bool { return x.to == to }) {
			se := &simEdge{id: id, from: from, to: to}
			from.out = append(from.out, se)
			to.in = append(to.in, se)
			edges[id] = se
			if from.Type == TypeQueue {
				from.subs = append(from.subs, &subscriber{edge: se})
			}
		}
	}
	return nodes, edges, nil
}

func sortedNodes(nodes map[string]*simNode) []*simNode {
	out := make([]*simNode, 0, len(nodes))
	for _, n := range nodes {
		out = append(out, n)
	}
	slices.SortFunc(out, func(a, b *simNode) int { return strings.Compare(a.ID, b.ID) })
	return out
}

// takeDown crashes n during [at, until); a database with a standby fails
// over sooner.
func (s *sim) takeDown(n *simNode, at, until float64) {
	if n.Type == TypeDatabase && n.Data.Replication != "" && n.Data.Replication != "none" {
		until = math.Min(until, at+FailoverMs)
	}
	n.downs = append(n.downs, [2]float64{at, until})
	s.schedule(&event{t: at, kind: crash, node: n})
	if !math.IsInf(until, 1) {
		s.schedule(&event{t: until, kind: recover, node: n})
	}
}

func (s *sim) applyChaos(c Chaos, nodes map[string]*simNode, edges map[string]*simEdge) error {
	for _, id := range c.Nodes {
		n := nodes[id]
		if n == nil {
			return fmt.Errorf("chaos: no node %q", id)
		}
		if n.Type == TypeClient {
			return fmt.Errorf("chaos: the Client can't be crashed")
		}
		s.log = append(s.log, Event{T: round1(c.AtMs), Kind: "crash", NodeID: n.ID, Message: fmt.Sprintf("Chaos: %s crashed", n.name())})
		s.takeDown(n, c.AtMs, math.Inf(1))
	}
	for _, id := range c.Edges {
		e := edges[id]
		if e == nil {
			return fmt.Errorf("chaos: no edge %q", id)
		}
		e.cuts = append(e.cuts, [2]float64{c.AtMs, math.Inf(1)})
		s.log = append(s.log, Event{T: round1(c.AtMs), Kind: "partition", EdgeID: id, Message: fmt.Sprintf("Chaos: the connection to %s was cut", e.to.name())})
	}
	return nil
}

// applyFaults schedules the scenario's faults against matching nodes and
// edges. A fault whose target isn't in the design does nothing.
func (s *sim) applyFaults(faults []Fault, nodes map[string]*simNode, edges map[string]*simEdge) {
	for _, f := range faults {
		until := math.Inf(1)
		if f.ForMs > 0 {
			until = f.AtMs + f.ForMs
		}
		switch f.Kind {
		case "crash":
			var targets []*simNode
			for _, n := range sortedNodes(nodes) {
				if (f.Node != "" && n.ID == f.Node) || (f.Node == "" && n.Type == f.Type) {
					targets = append(targets, n)
				}
			}
			if !f.All && len(targets) > 1 {
				targets = targets[:1]
			}
			for _, n := range targets {
				msg := f.Message
				if msg == "" {
					msg = fmt.Sprintf("%s crashed", n.name())
				}
				s.log = append(s.log, Event{T: round1(f.AtMs), Kind: "crash", NodeID: n.ID, Message: msg})
				s.takeDown(n, f.AtMs, until)
			}
		case "cut":
			var targets []*simEdge
			for _, n := range sortedNodes(nodes) {
				for _, e := range n.out {
					if (f.Edge != "" && e.id == f.Edge) || (f.Edge == "" && e.from.Type == f.From && e.to.Type == f.To) {
						targets = append(targets, e)
					}
				}
			}
			if !f.All && len(targets) > 1 {
				targets = targets[:1]
			}
			for _, e := range targets {
				msg := f.Message
				if msg == "" {
					msg = fmt.Sprintf("The network between %s and %s failed", e.from.name(), e.to.name())
				}
				e.cuts = append(e.cuts, [2]float64{f.AtMs, until})
				s.log = append(s.log, Event{T: round1(f.AtMs), Kind: "partition", EdgeID: e.id, Message: msg})
			}
		}
	}
}

// applyRollout drains and upgrades servers one at a time, in ID order.
func (s *sim) applyRollout(r *Rollout, nodes map[string]*simNode) {
	if r == nil {
		return
	}
	i := 0
	for _, n := range sortedNodes(nodes) {
		if n.Type != TypeServer || n.version(0) == r.To {
			continue
		}
		at := r.StartMs + float64(i)*r.IntervalMs
		n.drains = append(n.drains, [2]float64{at, at + r.RestartMs})
		n.upgradeAt, n.upgradeTo = at+r.RestartMs, r.To
		s.log = append(s.log, Event{T: round1(at), Kind: "deploy", NodeID: n.ID, Message: fmt.Sprintf("Deploying %s to %s", r.To, n.name())})
		i++
	}
}

func (s *sim) loadSchemas(sc Scenario, nodes map[string]*simNode) error {
	if sc.Schema == nil {
		return nil
	}
	s.schemas = map[string][]Field{"v1": sc.Schema.V1, "v2": sc.Schema.V1}
	var reg *simNode
	for _, n := range sortedNodes(nodes) {
		if n.Type == TypeSchemaRegistry {
			reg = n
			break
		}
	}
	if reg == nil {
		s.issue(nil, "no_schema_registry", "Add a Schema Registry so both app versions agree on the message format.")
	} else if len(reg.Data.Fields) > 0 {
		s.schemas["v2"] = reg.Data.Fields
	}
	if reg != nil {
		for _, name := range sc.Schema.NewFields {
			if !slices.ContainsFunc(s.schemas["v2"], func(f Field) bool { return f.Name == name }) {
				s.issue(reg, "schema_missing_"+name, fmt.Sprintf("The v2 schema needs a %q field: it's what the new version ships.", name))
			}
		}
	}
	for v := range sc.Traffic.ClientVersions {
		if _, ok := s.schemas[v]; !ok {
			return fmt.Errorf("traffic.client_versions: no schema for %q", v)
		}
	}
	return nil
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
	sc := opts.Scenario

	hasLB := false
	for _, n := range nodes {
		if n.Type == TypeLoadBalancer && n.processed > 0 {
			hasLB = true
		}
	}
	servedByServer := false
	for _, n := range sortedNodes(nodes) {
		st := NodeStats{Type: n.Type, Label: n.name(), Processed: n.processed}
		for _, sh := range n.shards {
			st.MaxQueue = max(st.MaxQueue, sh.maxQueue)
			if window := sh.lastDone - sh.firstStart; window > 0 {
				u := math.Min(1, busyBetween(sh.busySpans, sh.firstStart, sh.lastDone)/(float64(sh.workers)*window))
				st.Utilization = max(st.Utilization, math.Round(u*1000)/1000)
			}
		}
		if n.Type == TypeServer || n.Type == TypeDatabase {
			st.Pool = n.shards[0].workers
		}
		res.Nodes[n.ID] = st
		if n.Type == TypeServer && n.processed > 0 {
			servedByServer = true
		}
		pct := int(math.Round(st.Utilization * 100))
		// Busy nearly the whole run means demand exceeded capacity.
		switch {
		case st.Utilization < 0.95:
		case n.Type == TypeServer:
			msg := fmt.Sprintf("Server overloaded: %d%% CPU utilization. Add a Load Balancer.", pct)
			if hasLB {
				msg = fmt.Sprintf("%s is overloaded: %d%% CPU utilization. Add another server behind the load balancer.", n.name(), pct)
			}
			s.issue(n, "server_overloaded", msg)
		case n.Type == TypeDatabase && len(n.shards) > 1:
			s.issue(n, "database_overloaded", fmt.Sprintf("One partition of %s is %d%% busy: a hot key lands on a single partition. Cache hot reads.", n.name(), pct))
		case n.Type == TypeDatabase || n.Type == TypeReplica:
			s.issue(n, "database_overloaded", fmt.Sprintf("%s is overloaded: %d%% busy. Take reads off it with a cache or read replicas, or partition it.", n.name(), pct))
		case n.Type == TypeCache || n.Type == TypeSearchIndex:
			s.issue(n, "overloaded", fmt.Sprintf("%s is overloaded: %d%% busy.", n.name(), pct))
		}
	}
	if len(s.issues) == 0 && m.Completed > 0 && !servedByServer {
		s.issue(nil, "no_server", "Requests never reach a Server. Route traffic through an API server.")
	}
	allowed := int(math.Floor(float64(m.Requests) * sc.Goals.MaxFailedPct / 100))
	if m.Failed > allowed {
		msg := fmt.Sprintf("%s of %s requests never got a response.", commas(m.Failed), commas(m.Requests))
		if allowed > 0 {
			msg = fmt.Sprintf("%s of %s requests failed; at most %s (%g%%) may fail.", commas(m.Failed), commas(m.Requests), commas(allowed), sc.Goals.MaxFailedPct)
		}
		if s.userBlock > 0 {
			msg += fmt.Sprintf(" %s were real users turned away by a rate limiter.", commas(s.userBlock))
		}
		s.issue(nil, "failed_requests", msg)
	}
	if opts.MaxLatencyMs > 0 && m.Completed > 0 && m.P99Ms > opts.MaxLatencyMs {
		s.issue(nil, "latency", fmt.Sprintf("p99 latency is %.0f ms; the target is %.0f ms or less.", m.P99Ms, opts.MaxLatencyMs))
	}
	res.Cost.Budget = opts.MaxBudget
	if opts.MaxBudget > 0 && res.Cost.Total > opts.MaxBudget {
		s.issue(nil, "over_budget", fmt.Sprintf("This architecture costs $%d/month; the budget is $%d.", res.Cost.Total, opts.MaxBudget))
	}
	s.scenarioStats(&res, nodes, sc)

	keys := make([]string, 0, len(s.issues))
	for k := range s.issues {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	for _, k := range keys {
		res.Issues = append(res.Issues, s.issues[k])
	}
	// Overload is the root cause; show it first, and symptoms last.
	priority := func(code string) int {
		switch code {
		case "server_overloaded":
			return 0
		case "failed_requests", "latency":
			return 2
		}
		return 1
	}
	slices.SortStableFunc(res.Issues, func(a, b Issue) int { return priority(a.Code) - priority(b.Code) })

	res.Passed = len(res.Issues) == 0 && m.Requests > 0 && m.Completed+m.Failed == m.Requests
	if res.Passed {
		res.Message = fmt.Sprintf("Handled %s requests with p99 latency of %.0f ms.", commas(m.Requests), m.P99Ms)
	} else if len(res.Issues) > 0 {
		res.Message = res.Issues[0].Message
	} else {
		res.Message = "The simulation didn't finish."
	}
	res.Timeline = buildTimeline(s, nodes, edges)
	return res
}

// scenarioStats adds the measurements and goal checks for the node types
// and traffic in this run.
func (s *sim) scenarioStats(res *Result, nodes map[string]*simNode, sc Scenario) {
	stat := func(label, value string, good bool, judged bool) {
		st := Stat{Label: label, Value: value}
		if judged {
			st.Status = map[bool]string{true: "good", false: "bad"}[good]
		}
		res.Stats = append(res.Stats, st)
	}
	all := sortedNodes(nodes)
	if s.hasData && s.reads > 0 && sc.Goals.MaxStalePct != nil {
		pct := float64(s.stale) / float64(s.reads) * 100
		value := fmt.Sprintf("%.1f%% (%s of %s reads)", pct, commas(s.stale), commas(s.reads))
		if g := sc.Goals.MaxStalePct; g != nil {
			value += fmt.Sprintf(", target ≤ %g%%", *g)
			stat("Stale reads", value, pct <= *g, true)
			if pct > *g {
				var worst *simNode
				for _, n := range all {
					if n.stale > 0 && (worst == nil || n.stale > worst.stale) {
						worst = n
					}
				}
				why := ""
				switch {
				case worst == nil:
				case worst.Type == TypeReplica:
					why = fmt.Sprintf(" Most came from %s, which trails the primary by %d ms.", worst.name(), ReplicaLagMs)
				case worst.Type == TypeCache:
					why = fmt.Sprintf(" Most came from %s, which keeps serving entries after the data changes.", worst.name())
				}
				id := ""
				if worst != nil {
					id = worst.ID
				}
				s.issues["stale_reads"] = Issue{NodeID: id, Code: "stale_reads", Message: fmt.Sprintf("%.1f%% of reads returned outdated data; the target is %g%% or less.%s", pct, *g, why)}
			}
		} else {
			stat("Stale reads", value, false, false)
		}
	}
	for _, n := range all {
		switch n.Type {
		case TypeCache:
			if n.reads > 0 {
				stat(n.name()+" hit rate", fmt.Sprintf("%.0f%%", float64(n.hits)/float64(n.reads)*100), false, false)
			}
		case TypeCDN:
			if n.reads > 0 {
				stat(n.name()+" served", fmt.Sprintf("%.0f%% of static files", float64(n.hits)/float64(n.reads)*100), false, false)
			}
		case TypeQueue:
			peak := 0.0
			for _, b := range n.backlog {
				peak = max(peak, b[1])
			}
			stat(n.name()+" peak backlog", commas(int(peak))+" messages", false, false)
		case TypeSearchIndex:
			total, current := 0, 0
			for key, c := range s.commits {
				total++
				if n.indexed[key] == len(c) {
					current++
				}
			}
			if total == 0 {
				continue
			}
			ok := current == total
			stat(n.name(), fmt.Sprintf("%s of %s records up to date", commas(current), commas(total)), ok, true)
			if !ok {
				why := " Nothing sends it updates."
				if s.lostDual > 0 {
					why = fmt.Sprintf(" %s dual writes failed while it was unreachable and were never retried.", commas(s.lostDual))
				} else if current > 0 {
					why = ""
				}
				s.issue(n, "index_out_of_sync", fmt.Sprintf("%s is missing or out of date for %s of %s records.%s", n.name(), commas(total-current), commas(total), why))
			}
		}
	}
	if len(s.writeLat) > 0 && (sc.Goals.MaxWriteMs > 0 || len(s.lags) > 0) {
		slices.Sort(s.writeLat)
		p99 := percentile(s.writeLat, 99)
		value := fmt.Sprintf("%.0f ms p99", p99)
		if g := sc.Goals.MaxWriteMs; g > 0 {
			value += fmt.Sprintf(" (target ≤ %.0f ms)", g)
			stat("Write acknowledgment", value, p99 <= g, true)
			if p99 > g {
				s.issue(nil, "slow_writes", fmt.Sprintf("Writes take %.0f ms to be acknowledged (p99); the target is %.0f ms. Each write fans out to many records, so do that work asynchronously behind a message queue.", p99, g))
			}
		} else {
			stat("Write acknowledgment", value, false, false)
		}
	}
	if len(s.lags) > 0 || sc.Goals.MaxQueueLagMs > 0 {
		slices.Sort(s.lags)
		worst := 0.0
		if len(s.lags) > 0 {
			worst = s.lags[len(s.lags)-1]
		}
		value := fmt.Sprintf("%.0f ms max", worst)
		if g := sc.Goals.MaxQueueLagMs; g > 0 && len(s.lags) > 0 {
			value += fmt.Sprintf(" (target ≤ %.0f ms)", g)
			stat("Queue wait", value, worst <= g, true)
			if worst > g {
				s.issue(nil, "queue_lag", fmt.Sprintf("Writes waited up to %.1f s in the queue before a consumer picked them up; the target is %.1f s. The consumers can't keep up: add more, and give the database enough capacity (partitions) to absorb them.", worst/1000, g/1000))
			}
		} else if len(s.lags) > 0 {
			stat("Queue wait", value, false, false)
		}
	}
	for _, n := range all {
		if n.Type != TypeQueue {
			continue
		}
		for _, sub := range n.subs {
			stuck := len(n.topic) - sub.delivered
			if stuck == 0 {
				continue
			}
			to := sub.edge.to
			why := fmt.Sprintf("%s couldn't be reached", to.name())
			if to.isDown(math.MaxFloat64) {
				why = fmt.Sprintf("%s crashed and never came back", to.name())
				if to.Type == TypeDatabase {
					why += " (a standby replica would have taken over)"
				}
			}
			s.issue(n, "undelivered", fmt.Sprintf("%s still holds %s messages for %s: %s.", n.name(), commas(stuck), to.name(), why))
		}
	}
	if s.botSent > 0 {
		stat("Bot requests blocked", fmt.Sprintf("%s of %s", commas(s.botBlock), commas(s.botSent)), s.botBlock*2 >= s.botSent, true)
	}
	if s.userBlock > 0 {
		stat("Real users rate-limited", commas(s.userBlock), false, true)
	}
	if r := sc.Rollout; r != nil {
		total, upgraded := 0, 0
		for _, n := range all {
			if n.Type == TypeServer {
				total++
				if n.version(math.Inf(1)) == r.To {
					upgraded++
				}
			}
		}
		stat("Rolling deploy", fmt.Sprintf("%d of %d servers on %s", upgraded, total, r.To), upgraded == total && total > 0, true)
	}
	if s.schemas != nil {
		broken := 0
		for k := range s.issues {
			if strings.HasPrefix(k, "schema_") {
				broken++
			}
		}
		value := "v1 ⇄ v2 compatible"
		if broken > 0 {
			value = fmt.Sprintf("%d incompatible direction(s)", broken)
		}
		stat("Schema", value, broken == 0, true)
	}
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
