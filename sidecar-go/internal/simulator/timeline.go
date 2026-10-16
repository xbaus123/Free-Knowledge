package simulator

import (
	"fmt"
	"math"
	"slices"
)

// Event is something notable during a run, for the replay's markers.
type Event struct {
	T       float64 `json:"t"`
	Kind    string  `json:"kind"` // crash, partition, failover, bottleneck, queueing, errors, data_loss, stale, throttled, deploy, lock, write
	NodeID  string  `json:"nodeId,omitempty"`
	EdgeID  string  `json:"edgeId,omitempty"`
	Message string  `json:"message"`
}

// FrameNode is one node's state during a frame.
type FrameNode struct {
	Utilization float64 `json:"utilization"` // 0..1 of the worker pool (busiest partition), averaged over the frame
	Active      int     `json:"active"`      // requests in service at the frame's end
	Queue       int     `json:"queue"`       // requests (or queued messages) waiting at the frame's end
	Down        bool    `json:"down,omitempty"`
	// Badge is a short state label, like a server's app version.
	Badge string `json:"badge,omitempty"`
}

// Frame covers [T, T+interval).
type Frame struct {
	T         float64              `json:"t"`
	Nodes     map[string]FrameNode `json:"nodes"`
	Edges     map[string]int       `json:"edges"` // requests sent over each edge
	Completed int                  `json:"completed"`
	Failed    int                  `json:"failed"`
}

type Timeline struct {
	IntervalMs float64 `json:"intervalMs"`
	Frames     []Frame `json:"frames"`
	Events     []Event `json:"events"`
}

const targetFrames = 60

// frameInterval picks a round frame length giving about targetFrames frames.
func frameInterval(end float64) float64 {
	raw := end / targetFrames
	for _, step := range []float64{5, 10, 20, 25, 50, 100, 200, 250, 500, 1000} {
		if raw <= step {
			return step
		}
	}
	return math.Ceil(raw/1000) * 1000
}

func buildTimeline(s *sim, nodes map[string]*simNode, edges map[string]*simEdge) Timeline {
	tl := Timeline{Frames: []Frame{}, Events: slices.Clone(s.log)}
	if tl.Events == nil {
		tl.Events = []Event{}
	}
	if s.end <= 0 {
		return tl
	}
	tl.IntervalMs = frameInterval(s.end)
	count := int(math.Ceil(s.end / tl.IntervalMs))

	slices.Sort(s.doneTimes)
	slices.Sort(s.failTimes)
	for _, e := range edges {
		slices.Sort(e.requests)
	}
	bottlenecked := map[string]bool{}
	for i := range count {
		a := float64(i) * tl.IntervalMs
		b := a + tl.IntervalMs
		f := Frame{T: a, Nodes: map[string]FrameNode{}, Edges: map[string]int{}}
		for id, n := range nodes {
			if n.Type == TypeClient || n.Type == TypeSchemaRegistry {
				continue
			}
			fn := FrameNode{Down: n.isDown(b-0.001) || n.isDraining(b-0.001)}
			for _, sh := range n.shards {
				fn.Queue += queueAt(sh.queueLog, b)
				u := math.Round(busyBetween(sh.busySpans, a, b)/(float64(sh.workers)*tl.IntervalMs)*1000) / 1000
				fn.Utilization = max(fn.Utilization, u)
				for _, span := range sh.busySpans {
					if span[0] <= b && b < span[1] {
						fn.Active++
					}
				}
			}
			if n.Type == TypeQueue {
				fn.Queue = queueAt(n.backlog, b)
			}
			if n.Type == TypeServer && (s.schemas != nil || n.upgradeTo != "") {
				fn.Badge = n.version(b - 0.001)
			}
			if fn.Utilization >= 0.95 && !bottlenecked[id] && n.Type != TypeSearchIndex {
				bottlenecked[id] = true
				tl.Events = append(tl.Events, Event{T: a, Kind: "bottleneck", NodeID: id, Message: fmt.Sprintf("%s hit full capacity", n.name())})
			}
			f.Nodes[id] = fn
		}
		for id, e := range edges {
			if c := countIn(e.requests, a, b); c > 0 {
				f.Edges[id] = c
			}
		}
		f.Completed = countIn(s.doneTimes, a, b)
		f.Failed = countIn(s.failTimes, a, b)
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
	return tl
}

// busyBetween sums worker-time spent in service within [a, b).
func busyBetween(spans [][2]float64, a, b float64) float64 {
	total := 0.0
	for _, s := range spans {
		if lo, hi := max(s[0], a), min(s[1], b); hi > lo {
			total += hi - lo
		}
	}
	return total
}

// queueAt returns the queue length at time t from a time-ordered log.
func queueAt(log [][2]float64, t float64) int {
	q := 0
	for _, entry := range log {
		if entry[0] > t {
			break
		}
		q = int(entry[1])
	}
	return q
}

// countIn counts sorted times within [a, b).
func countIn(sorted []float64, a, b float64) int {
	lo, _ := slices.BinarySearch(sorted, a)
	hi, _ := slices.BinarySearch(sorted, b)
	return hi - lo
}
