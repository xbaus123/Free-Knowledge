package simulator

import (
	"fmt"
	"math/rand/v2"
	"slices"
)

// Scenario is a lesson's simulation setup, from the "simulation" object in
// its config.json. The zero value is the original scalability lesson: a
// burst of reads with no faults.
type Scenario struct {
	// Kind is "" or "traffic" for the traffic simulator, or "fencing" for
	// the distributed lock scenario.
	Kind string `json:"kind,omitempty"`
	// Palette lists the node types the canvas offers (frontend only);
	// empty means client, load balancer, server, and database.
	Palette []string `json:"palette,omitempty"`
	Traffic Traffic  `json:"traffic"`
	// Faults are part of the graded run (unlike chaos experiments).
	Faults  []Fault     `json:"faults,omitempty"`
	Rollout *Rollout    `json:"rollout,omitempty"`
	Schema  *SchemaSpec `json:"schema,omitempty"`
	Goals   Goals       `json:"goals"`
}

// Traffic describes the requests the Client sends.
type Traffic struct {
	Requests   int     `json:"requests,omitempty"`    // base requests, spread evenly
	DurationMs float64 `json:"duration_ms,omitempty"` // over this window
	// Mix weights the request classes: "read", "write", and "static"
	// (images and scripts a CDN can serve). Default: all reads.
	Mix map[string]float64 `json:"mix,omitempty"`
	// Keys is how many distinct records reads and writes touch. Reads
	// favor popular records (a Zipf distribution); writes are uniform.
	// Default 1,000.
	Keys int `json:"keys,omitempty"`
	// Users is how many distinct users send the base traffic; rate
	// limiters count requests per user. Default 1,000.
	Users int `json:"users,omitempty"`
	// ReadYourWritesMs, if set, makes each writer read the same record
	// back this long after writing it.
	ReadYourWritesMs float64 `json:"read_your_writes_ms,omitempty"`
	// ClientVersions weights the app versions clients run ("v1", "v2"),
	// for schema evolution lessons.
	ClientVersions map[string]float64 `json:"client_versions,omitempty"`
	// WriteCost multiplies a database's work for each write, for writes
	// that fan out to many records (like a post copied into every
	// follower's timeline). Default 1.
	WriteCost int     `json:"write_cost,omitempty"`
	Spikes    []Spike `json:"spikes,omitempty"`
}

// Spike adds extra traffic for a while.
type Spike struct {
	AtMs  float64 `json:"at_ms"`
	ForMs float64 `json:"for_ms"`
	// Multiplier scales the base request rate during the spike: 100 means
	// 99 extra requests for every normal one.
	Multiplier float64 `json:"multiplier"`
	// Kind: "hot_key" (everyone reads one viral record), "bot" (one
	// client hammers the API), or "all" (more of the normal mix).
	Kind string `json:"kind"`
}

// Fault breaks something at a set time during a graded run.
type Fault struct {
	// Kind is "crash" (a node goes down) or "cut" (a connection drops).
	Kind string `json:"kind"`
	// Node targets one node by ID; Type targets nodes of that type.
	Node string `json:"node,omitempty"`
	Type string `json:"type,omitempty"`
	// All applies to every match instead of the first (by ID).
	All bool `json:"all,omitempty"`
	// Cuts: the connection from a node of type From to one of type To,
	// or Edge by ID.
	From  string  `json:"from,omitempty"`
	To    string  `json:"to,omitempty"`
	Edge  string  `json:"edge,omitempty"`
	AtMs  float64 `json:"at_ms"`
	ForMs float64 `json:"for_ms,omitempty"` // 0: for the rest of the run
	// Message describes the fault on the timeline.
	Message string `json:"message,omitempty"`
}

// Rollout upgrades servers one at a time (a rolling deployment).
type Rollout struct {
	To         string  `json:"to"`          // the new version, e.g. "v2"
	StartMs    float64 `json:"start_ms"`    // when the first server drains
	IntervalMs float64 `json:"interval_ms"` // between servers
	RestartMs  float64 `json:"restart_ms"`  // how long each is out of rotation
}

// Goals are a lesson's extra pass conditions.
type Goals struct {
	// MaxStalePct fails the run if more reads than this percentage
	// return outdated data.
	MaxStalePct *float64 `json:"max_stale_pct,omitempty"`
	// MaxFailedPct tolerates some failed requests (faults make a few
	// inevitable). Default 0.
	MaxFailedPct float64 `json:"max_failed_pct,omitempty"`
	// MaxWriteMs fails the run if writes take longer than this to be
	// acknowledged (p99).
	MaxWriteMs float64 `json:"max_write_ms,omitempty"`
	// MaxQueueLagMs fails the run if a write waits in a message queue
	// longer than this before a consumer picks it up.
	MaxQueueLagMs float64 `json:"max_queue_lag_ms,omitempty"`
	// Require lists node types the design must include.
	Require []string `json:"require,omitempty"`
}

// Request classes.
const (
	ClassRead   = "read"
	ClassWrite  = "write"
	ClassStatic = "static"
)

const (
	staticAssets = 20 // distinct images and scripts
	botUser      = -1
)

func (sc Scenario) withDefaults() Scenario {
	t := &sc.Traffic
	if t.Requests <= 0 {
		t.Requests = 1000
	}
	if t.DurationMs <= 0 {
		t.DurationMs = 1000
		if sc.Kind == "fencing" {
			t.DurationMs = fenceDurationMs
		}
	}
	if len(t.Mix) == 0 {
		t.Mix = map[string]float64{ClassRead: 1}
	}
	if t.Keys <= 0 {
		t.Keys = 1000
	}
	if t.Users <= 0 {
		t.Users = 1000
	}
	return sc
}

// Validate checks a scenario's settings.
func (sc Scenario) Validate() error {
	switch sc.Kind {
	case "", "traffic", "fencing":
	default:
		return fmt.Errorf("unknown simulation kind %q", sc.Kind)
	}
	for _, p := range sc.Palette {
		if _, ok := catalog[p]; !ok {
			return fmt.Errorf("palette: unknown node type %q", p)
		}
	}
	t := sc.Traffic
	if t.Requests < 0 || t.Requests > 50000 {
		return fmt.Errorf("traffic.requests must be between 1 and 50,000")
	}
	if t.WriteCost < 0 || t.WriteCost > 1000 {
		return fmt.Errorf("traffic.write_cost must be between 1 and 1,000")
	}
	if t.DurationMs < 0 || t.DurationMs > 10000 {
		return fmt.Errorf("traffic.duration_ms must be at most 10,000")
	}
	for class, w := range t.Mix {
		if !slices.Contains([]string{ClassRead, ClassWrite, ClassStatic}, class) || w < 0 {
			return fmt.Errorf("traffic.mix: %q must be read, write, or static with a non-negative weight", class)
		}
	}
	for v, w := range t.ClientVersions {
		if v == "" || w < 0 {
			return fmt.Errorf("traffic.client_versions: invalid entry %q", v)
		}
	}
	extra := 0.0
	for _, s := range t.Spikes {
		if !slices.Contains([]string{"hot_key", "bot", "all"}, s.Kind) {
			return fmt.Errorf("spike kind must be hot_key, bot, or all")
		}
		if s.Multiplier < 1 || s.Multiplier > 1000 || s.ForMs <= 0 {
			return fmt.Errorf("spikes need a multiplier from 1 to 1,000 and a positive for_ms")
		}
		extra += (s.Multiplier - 1) * s.ForMs
	}
	if base := max(t.DurationMs, 1); float64(max(t.Requests, 1000))*extra/base > 100000 {
		return fmt.Errorf("spikes add too many requests (limit 100,000)")
	}
	for _, f := range sc.Faults {
		if f.Kind != "crash" && f.Kind != "cut" && !(sc.Kind == "fencing" && f.Kind == "pause") {
			return fmt.Errorf("fault kind must be crash or cut")
		}
	}
	if r := sc.Rollout; r != nil && (r.To == "" || r.IntervalMs <= 0 || r.RestartMs <= 0) {
		return fmt.Errorf("rollout needs to, interval_ms, and restart_ms")
	}
	if sc.Schema != nil {
		if err := validateSchema(sc.Schema.V1); err != nil {
			return fmt.Errorf("schema.v1: %w", err)
		}
	}
	for _, r := range sc.Goals.Require {
		if _, ok := catalog[r]; !ok {
			return fmt.Errorf("goals.require: unknown node type %q", r)
		}
	}
	return nil
}

// arrival is one request the Client will send.
type arrival struct {
	t       float64
	class   string
	key     int
	user    int
	version string
}

// arrivals generates the scenario's traffic, sorted by time. It's
// deterministic: the same scenario always produces the same requests.
func (t Traffic) arrivals() []arrival {
	rng := rand.New(rand.NewPCG(1, 2))
	zipf := rand.NewZipf(rng, 1.1, 1, uint64(t.Keys-1))
	classes, weights := weighted(t.Mix)
	versions, vweights := weighted(t.ClientVersions)

	pick := func(names []string, w []float64) string {
		if len(names) == 1 {
			return names[0]
		}
		x := rng.Float64() * w[len(w)-1]
		i, _ := slices.BinarySearch(w, x)
		return names[min(i, len(names)-1)]
	}
	newArrival := func(at float64, class string) arrival {
		a := arrival{t: at, class: class, user: rng.IntN(t.Users)}
		switch class {
		case ClassStatic:
			a.key = rng.IntN(staticAssets)
		case ClassWrite:
			// New posts and updates spread evenly; reads favor
			// popular records.
			a.key = rng.IntN(t.Keys)
		default:
			a.key = int(zipf.Uint64())
		}
		if len(versions) > 0 {
			a.version = pick(versions, vweights)
		}
		return a
	}

	var out []arrival
	interval := t.DurationMs / float64(t.Requests)
	for i := range t.Requests {
		a := newArrival(float64(i)*interval, pick(classes, weights))
		out = append(out, a)
		if a.class == ClassWrite && t.ReadYourWritesMs > 0 {
			back := a
			back.t, back.class = a.t+t.ReadYourWritesMs, ClassRead
			out = append(out, back)
		}
	}
	for _, s := range t.Spikes {
		n := int((s.Multiplier - 1) * s.ForMs / interval)
		step := s.ForMs / float64(max(n, 1))
		for i := range n {
			at := s.AtMs + float64(i)*step
			switch s.Kind {
			case "hot_key":
				a := newArrival(at, ClassRead)
				a.key = 0
				out = append(out, a)
			case "bot":
				a := newArrival(at, ClassRead)
				a.user = botUser
				out = append(out, a)
			default:
				out = append(out, newArrival(at, pick(classes, weights)))
			}
		}
	}
	slices.SortStableFunc(out, func(a, b arrival) int {
		switch {
		case a.t < b.t:
			return -1
		case a.t > b.t:
			return 1
		}
		return 0
	})
	return out
}

// weighted returns a map's keys (sorted) with cumulative weights.
func weighted(m map[string]float64) ([]string, []float64) {
	var names []string
	for k, w := range m {
		if w > 0 {
			names = append(names, k)
		}
	}
	slices.Sort(names)
	cum := make([]float64, len(names))
	total := 0.0
	for i, k := range names {
		total += m[k]
		cum[i] = total
	}
	return names, cum
}
