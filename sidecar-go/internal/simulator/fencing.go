package simulator

import (
	"fmt"
	"math"
	"slices"
)

// The fencing scenario: workers take turns holding a lease from a lock
// service and write to storage while they hold it. The scenario's faults
// pause one worker (think of a long garbage collection pause) and drop its
// packets to the lock service, so its lease expires without it noticing.
// When it wakes up, it sends the write it had prepared. Safe designs give
// each lease a fencing token and have storage reject writes carrying an
// older token than one it has already seen.

const (
	fenceTickMs       = 10
	fenceRetryMs      = 50 // workers retry acquiring the lock
	fenceWriteMs      = 50 // lock holders write this often
	fenceMaxStallMs   = 1000
	fenceDurationMs   = 3000
	fenceFirstToken   = 33
	fenceFrameMs      = 50
	fenceAcquireLabel = "acquire"
)

type fenceWorker struct {
	*simNode
	lockEdge, storeEdge *simEdge
	holds               bool
	grant, token        int     // lease number, and its fencing token (0 without fencing)
	leaseUntil          float64 // when the worker believes its lease ends
	nextTry, nextWrite  float64
	nextRenew           float64
	pauses              [][2]float64
	pending             bool // a write prepared before a pause
	pendingGrant        int
	pendingToken        int
}

type fenceWrite struct {
	w            *fenceWorker
	grant, token int
	at           float64
}

func runFencing(g Graph, opts Options, cost CostBreakdown) (Result, error) {
	nodes, edges, err := build(g)
	if err != nil {
		return Result{}, err
	}
	res := Result{Issues: []Issue{}, Stats: []Stat{}, Nodes: map[string]NodeStats{}, Cost: cost, Experiment: !opts.Chaos.Empty()}
	s := &sim{issues: map[string]Issue{}, logged: map[string]bool{}}
	duration := opts.Scenario.Traffic.DurationMs
	if err := s.applyChaos(opts.Chaos, nodes, edges); err != nil {
		return Result{}, err
	}
	s.applyFaults(opts.Scenario.Faults, nodes, edges)
	s.events = nil // crash events are handled by polling isDown below

	var lock, store *simNode
	var workers []*fenceWorker
	for _, n := range sortedNodes(nodes) {
		switch n.Type {
		case TypeLock:
			if lock == nil {
				lock = n
			}
		case TypeDatabase:
			if store == nil {
				store = n
			}
		case TypeServer:
			workers = append(workers, &fenceWorker{simNode: n})
		}
	}
	for _, f := range opts.Scenario.Faults {
		if f.Kind != "pause" {
			continue
		}
		for _, w := range workers {
			if w.ID == f.Node || (f.Node == "" && f.Type == TypeServer) {
				end := f.AtMs + f.ForMs
				w.pauses = append(w.pauses, [2]float64{f.AtMs, end})
				msg := f.Message
				if msg == "" {
					msg = fmt.Sprintf("%s froze (a long garbage collection pause)", w.name())
				}
				s.log = append(s.log, Event{T: f.AtMs, Kind: "crash", NodeID: w.ID, Message: msg})
				s.log = append(s.log, Event{T: end, Kind: "failover", NodeID: w.ID, Message: fmt.Sprintf("%s woke up, unaware that time passed", w.name())})
				break
			}
		}
	}

	switch {
	case lock == nil:
		s.issue(nil, "missing_lock", "Add a Lock Service so only one worker writes at a time.")
	case store == nil:
		s.issue(nil, "missing_storage", "Add a database for the workers to write to.")
	case len(workers) < 2:
		s.issue(nil, "missing_workers", "This scenario needs two workers (servers) competing for the lock.")
	}
	lease := float64(catalog[TypeLock].DefaultLeaseMs)
	if lock != nil && lock.Data.LeaseMs > 0 {
		lease = float64(lock.Data.LeaseMs)
	}
	for _, w := range workers {
		for _, e := range w.out {
			if lock != nil && e.to == lock {
				w.lockEdge = e
			}
			if store != nil && e.to == store {
				w.storeEdge = e
			}
		}
		if lock != nil && w.lockEdge == nil {
			s.issue(w.simNode, "unlocked_writes", fmt.Sprintf("%s writes without taking the lock. Connect it to %s.", w.name(), lock.name()))
		}
	}
	if len(s.issues) > 0 {
		res.Message = s.sortedIssues(&res)
		res.Timeline = Timeline{Frames: []Frame{}, Events: []Event{}}
		return res, nil
	}

	fencing, checking := lock.Data.Fencing, store.Data.CheckTokens
	var holder *fenceWorker
	var holderUntil float64
	grants, nextToken := 0, fenceFirstToken
	maxGrant, maxToken := 0, 0
	var accepted, rejected, corrupted, sent int
	var lastAccept float64
	longestStall, stallFrom := 0.0, 0.0
	var lastWriter *fenceWorker
	var inflight []fenceWrite
	var acceptTimes []float64

	type snapshot struct {
		holder, writer string
		token          int
	}
	frames := map[int]snapshot{}
	badges := map[string]map[int]string{}
	setBadge := func(id string, t float64, b string) {
		if badges[id] == nil {
			badges[id] = map[int]string{}
		}
		badges[id][int(t/fenceFrameMs)] = b
	}
	paused := func(w *fenceWorker, t float64) bool { return within(w.pauses, t) || w.isDown(t) }

	send := func(e *simEdge, t float64) bool {
		if e == nil {
			return false
		}
		e.requests = append(e.requests, t)
		return !e.isCut(t) && !e.to.isDown(t)
	}

	for t := 0.0; t <= duration; t += fenceTickMs {
		// Storage applies writes that have arrived.
		keep := inflight[:0]
		for _, wr := range inflight {
			if wr.at > t {
				keep = append(keep, wr)
				continue
			}
			if checking && wr.token < maxToken {
				rejected++
				wr.w.holds = false
				s.event(t, "lock", store.ID, "", fmt.Sprintf("%s rejected a write from %s with stale token %d (it has seen %d)", store.name(), wr.w.name(), wr.token, maxToken))
				continue
			}
			if wr.grant < maxGrant {
				corrupted++
				who := "another worker"
				if lastWriter != nil {
					who = lastWriter.name()
				}
				s.issue(wr.w.simNode, "corrupted_write", fmt.Sprintf("%s's lease had expired, but its delayed write still overwrote %s's newer data. Use fencing tokens: the lock service issues them, and storage rejects older ones.", wr.w.name(), who))
				s.event(t, "data_loss", store.ID, "", fmt.Sprintf("%s's stale write overwrote %s's data", wr.w.name(), who))
			}
			maxGrant = max(maxGrant, wr.grant)
			maxToken = max(maxToken, wr.token)
			accepted++
			acceptTimes = append(acceptTimes, t)
			if lastAccept > 0 {
				if gap := t - lastAccept; gap > longestStall {
					longestStall, stallFrom = gap, lastAccept
				}
			}
			lastAccept = t
			lastWriter = wr.w
		}
		inflight = keep
		if holder != nil && t >= holderUntil {
			s.event(t, "lock", lock.ID, "", fmt.Sprintf("%s's lease expired", holder.name()))
			holder = nil
		}

		for _, w := range workers {
			if paused(w, t) {
				if w.holds && !w.pending && w.storeEdge != nil {
					// It had checked its lease and prepared this write
					// just before freezing.
					w.pending, w.pendingGrant, w.pendingToken = true, w.grant, w.token
				}
				setBadge(w.ID, t, "paused")
				continue
			}
			if w.pending {
				w.pending = false
				sent++
				if send(w.storeEdge, t) {
					inflight = append(inflight, fenceWrite{w: w, grant: w.pendingGrant, token: w.pendingToken, at: t + HopMs})
				}
				w.nextWrite = t + fenceWriteMs
			}
			if w.lockEdge == nil {
				// No lock: it just writes.
				w.holds, w.grant = true, 0
				w.leaseUntil = math.Inf(1)
			}
			if w.holds && t >= w.leaseUntil {
				w.holds = false
			}
			if !w.holds && t >= w.nextTry {
				w.nextTry = t + fenceRetryMs
				if send(w.lockEdge, t) && (holder == nil || holder == w) {
					grants++
					holder, holderUntil = w, t+lease
					w.holds, w.grant, w.leaseUntil = true, grants, t+lease
					w.token = 0
					if fencing {
						w.token = nextToken
						nextToken++
					}
					w.nextRenew, w.nextWrite = t+lease/3, t
					msg := fmt.Sprintf("%s acquired the lock", w.name())
					if fencing {
						msg += fmt.Sprintf(" (token %d)", w.token)
					}
					s.log = append(s.log, Event{T: t, Kind: "lock", NodeID: w.ID, Message: msg})
				}
			}
			if w.holds && w.lockEdge != nil && t >= w.nextRenew {
				w.nextRenew = t + lease/3
				if send(w.lockEdge, t) {
					if holder == w {
						holderUntil, w.leaseUntil = t+lease, t+lease
					} else {
						w.holds = false // someone else has it now
					}
				}
			}
			if w.holds && t >= w.nextWrite && w.storeEdge != nil {
				w.nextWrite = t + fenceWriteMs
				sent++
				if send(w.storeEdge, t) {
					inflight = append(inflight, fenceWrite{w: w, grant: w.grant, token: w.token, at: t + HopMs})
				}
			}
			switch {
			case w.holds && fencing:
				setBadge(w.ID, t, fmt.Sprintf("🔒 token %d", w.token))
			case w.holds:
				setBadge(w.ID, t, "🔒 holds lock")
			default:
				setBadge(w.ID, t, "waiting")
			}
		}
		snap := snapshot{}
		if holder != nil {
			snap.holder, snap.token = holder.name(), holder.token
		}
		if lastWriter != nil {
			snap.writer = lastWriter.name()
		}
		frames[int(t/fenceFrameMs)] = snap
	}
	if lastAccept > 0 && duration-lastAccept > longestStall {
		longestStall, stallFrom = duration-lastAccept, lastAccept
	}
	if accepted == 0 {
		s.issue(store, "no_progress", "No writes reached storage. Connect the workers to it.")
	} else if longestStall > fenceMaxStallMs {
		s.issue(lock, "stalled", fmt.Sprintf("No worker could write for %.2f s (from %.2f s): the lease is too long, so the lock stayed with a frozen worker. Shorten it to %d ms or less.", longestStall/1000, stallFrom/1000, fenceMaxStallMs))
	}
	if corrupted > 0 {
		switch {
		case fencing && !checking:
			s.issue(store, "tokens_unchecked", fmt.Sprintf("The lock service issues fencing tokens, but %s doesn't check them. Turn on token checking.", store.name()))
		case checking && !fencing:
			s.issue(lock, "no_tokens", fmt.Sprintf("%s checks fencing tokens, but %s doesn't issue any. Turn on fencing tokens.", store.name(), lock.name()))
		}
	}

	// Results.
	m := &res.Metrics
	m.Requests, m.Completed = sent, accepted
	m.DurationMs = duration
	stat := func(label, value string, status string) {
		res.Stats = append(res.Stats, Stat{Label: label, Value: value, Status: status})
	}
	stat("Lease", fmt.Sprintf("%.1f s", lease/1000), "")
	stat("Writes accepted", commas(accepted), "")
	if rejected > 0 || checking {
		stat("Stale writes rejected", commas(rejected), "good")
	}
	stat("Corrupted writes", commas(corrupted), map[bool]string{true: "good", false: "bad"}[corrupted == 0])
	stat("Longest stall", fmt.Sprintf("%.2f s (limit %.1f s)", longestStall/1000, fenceMaxStallMs/1000.0), map[bool]string{true: "good", false: "bad"}[longestStall <= fenceMaxStallMs])
	for _, n := range sortedNodes(nodes) {
		res.Nodes[n.ID] = NodeStats{Type: n.Type, Label: n.name()}
	}
	res.Message = s.sortedIssues(&res)
	res.Passed = len(res.Issues) == 0
	if res.Passed {
		res.Message = fmt.Sprintf("No corrupted writes, and the work never stalled longer than %.2f s.", longestStall/1000)
	}

	// Timeline.
	tl := Timeline{IntervalMs: fenceFrameMs, Frames: []Frame{}, Events: s.log}
	for i := 0; float64(i)*fenceFrameMs < duration; i++ {
		a, b := float64(i)*fenceFrameMs, float64(i+1)*fenceFrameMs
		f := Frame{T: a, Nodes: map[string]FrameNode{}, Edges: map[string]int{}}
		for id, n := range nodes {
			fn := FrameNode{Down: n.isDown(b - 0.001)}
			if bs := badges[id]; bs != nil {
				fn.Badge = bs[i]
				if fn.Badge == "paused" {
					fn.Down = true
				}
			}
			snap := frames[i]
			if n == lock {
				fn.Badge = "free"
				if snap.holder != "" {
					fn.Badge = snap.holder
					if fencing {
						fn.Badge += fmt.Sprintf(" · %d", snap.token)
					}
				}
			}
			if n == store && snap.writer != "" {
				fn.Badge = "last: " + snap.writer
			}
			f.Nodes[id] = fn
		}
		for id, e := range edges {
			if c := countIn(e.requests, a, b); c > 0 {
				f.Edges[id] = c
			}
		}
		f.Completed = countIn(acceptTimes, a, b) // writes storage accepted
		tl.Frames = append(tl.Frames, f)
	}
	slices.SortStableFunc(tl.Events, func(x, y Event) int {
		switch {
		case x.T < y.T:
			return -1
		case x.T > y.T:
			return 1
		}
		return 0
	})
	if len(tl.Events) > maxEvents {
		tl.Events = tl.Events[:maxEvents]
	}
	res.Timeline = tl
	return res, nil
}

// sortedIssues moves s.issues into res in a stable order and returns the
// first message.
func (s *sim) sortedIssues(res *Result) string {
	keys := make([]string, 0, len(s.issues))
	for k := range s.issues {
		keys = append(keys, k)
	}
	slices.Sort(keys)
	for _, k := range keys {
		res.Issues = append(res.Issues, s.issues[k])
	}
	if len(res.Issues) > 0 {
		return res.Issues[0].Message
	}
	return ""
}
