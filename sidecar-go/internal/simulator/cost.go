package simulator

import (
	"fmt"
	"slices"
)

// NodeSpec describes a node type: what it costs and how it performs.
type NodeSpec struct {
	Type      string  `json:"type"`
	Name      string  `json:"name"`
	Cost      int     `json:"cost"`      // $/month for the default setup
	Workers   int     `json:"workers"`   // requests served at once; 0 = unlimited
	ServiceMs float64 `json:"serviceMs"` // time to handle one request
	// Servers: the connection pool can be resized; each slot past the
	// default costs PoolSlotCost, so scaling up gets expensive.
	MinPool      int `json:"minPool,omitempty"`
	MaxPool      int `json:"maxPool,omitempty"`
	PoolSlotCost int `json:"poolSlotCost,omitempty"`
	// Databases: a standby replica (sync or async) costs this much more,
	// and the data can be split into up to MaxPartitions partitions,
	// each priced and sized like a whole database.
	ReplicaCost   int `json:"replicaCost,omitempty"`
	MaxPartitions int `json:"maxPartitions,omitempty"`
	// Rate limiters: the default requests per second allowed per user.
	DefaultLimit int `json:"defaultLimit,omitempty"`
	// Queues: deliveries in flight to each subscriber at once.
	DefaultConsumers int `json:"defaultConsumers,omitempty"`
	MaxConsumers     int `json:"maxConsumers,omitempty"`
	// Caches: how long entries live under the "ttl" policy.
	DefaultTTLMs int `json:"defaultTtlMs,omitempty"`
	// Lock services: the default lease length.
	DefaultLeaseMs int `json:"defaultLeaseMs,omitempty"`
}

// More node types.
const (
	TypeCDN            = "cdn"
	TypeRateLimiter    = "rateLimiter"
	TypeCache          = "cache"
	TypeReplica        = "replica"
	TypeQueue          = "queue"
	TypeSearchIndex    = "searchIndex"
	TypeLock           = "lock"
	TypeSchemaRegistry = "schemaRegistry"
)

// The catalog is tuned so one default server can't absorb the first
// lesson's burst (4 workers / 6 ms ≈ 667 req/s against 1,000 req/s) but
// two can, and so a database (10 connections / 4 ms = 2,500 queries/s)
// needs help under read-heavy load.
var catalog = map[string]NodeSpec{
	TypeClient:         {Type: TypeClient, Name: "Client"},
	TypeCDN:            {Type: TypeCDN, Name: "CDN", Cost: 15, ServiceMs: 1},
	TypeRateLimiter:    {Type: TypeRateLimiter, Name: "Rate Limiter", Cost: 10, ServiceMs: 0.5, DefaultLimit: 20},
	TypeLoadBalancer:   {Type: TypeLoadBalancer, Name: "Load Balancer", Cost: 20, ServiceMs: 1},
	TypeServer:         {Type: TypeServer, Name: "Server", Cost: 10, Workers: 4, ServiceMs: 6, MinPool: 1, MaxPool: 32, PoolSlotCost: 10},
	TypeCache:          {Type: TypeCache, Name: "Cache", Cost: 25, Workers: 20, ServiceMs: 0.5, DefaultTTLMs: 60000},
	TypeDatabase:       {Type: TypeDatabase, Name: "Database", Cost: 50, Workers: 10, ServiceMs: 4, ReplicaCost: 40, MaxPartitions: 8},
	TypeReplica:        {Type: TypeReplica, Name: "Read Replica", Cost: 40, Workers: 10, ServiceMs: 4},
	TypeQueue:          {Type: TypeQueue, Name: "Message Queue", Cost: 20, ServiceMs: 0.5, DefaultConsumers: 4, MaxConsumers: 32},
	TypeSearchIndex:    {Type: TypeSearchIndex, Name: "Search Index", Cost: 30, Workers: 10, ServiceMs: 5},
	TypeLock:           {Type: TypeLock, Name: "Lock Service", Cost: 15, ServiceMs: 1, DefaultLeaseMs: 10000},
	TypeSchemaRegistry: {Type: TypeSchemaRegistry, Name: "Schema Registry", Cost: 5},
}

var catalogOrder = []string{
	TypeClient, TypeCDN, TypeRateLimiter, TypeLoadBalancer, TypeServer, TypeCache, TypeDatabase,
	TypeReplica, TypeQueue, TypeSearchIndex, TypeLock, TypeSchemaRegistry,
}

// Catalog lists the node types, for the canvas's palette and price tags.
func Catalog() []NodeSpec {
	out := []NodeSpec{}
	for _, t := range catalogOrder {
		out = append(out, catalog[t])
	}
	return out
}

type CostItem struct {
	NodeID string `json:"nodeId"`
	Label  string `json:"label"`
	Cost   int    `json:"cost"`
	Detail string `json:"detail,omitempty"`
}

// CostBreakdown is an architecture's monthly cost.
type CostBreakdown struct {
	Total  int        `json:"total"`
	Budget int        `json:"budget,omitempty"`
	Items  []CostItem `json:"items"`
}

// Cost prices g, validating node types and settings.
func Cost(g Graph) (CostBreakdown, error) {
	out := CostBreakdown{Items: []CostItem{}}
	for _, n := range g.Nodes {
		spec, ok := catalog[n.Type]
		if !ok {
			return out, fmt.Errorf("unknown node type %q", n.Type)
		}
		if err := validateSettings(n, spec); err != nil {
			return out, fmt.Errorf("%s: %w", n.ID, err)
		}
		item := CostItem{NodeID: n.ID, Label: n.Data.Label, Cost: spec.Cost}
		var details []string
		switch n.Type {
		case TypeServer:
			if extra := n.Data.Pool - spec.Workers; n.Data.Pool != 0 && extra > 0 {
				item.Cost += extra * spec.PoolSlotCost
				details = append(details, fmt.Sprintf("%d-connection pool (+$%d)", n.Data.Pool, extra*spec.PoolSlotCost))
			}
		case TypeDatabase:
			parts := max(1, n.Data.Partitions)
			if parts > 1 {
				item.Cost = spec.Cost * parts
				details = append(details, fmt.Sprintf("%d partitions", parts))
			}
			if r := n.Data.Replication; r == "sync" || r == "async" {
				item.Cost += spec.ReplicaCost * parts
				details = append(details, fmt.Sprintf("%s standby (+$%d)", r, spec.ReplicaCost*parts))
			}
		}
		if len(details) > 0 {
			item.Detail = joinComma(details)
		}
		out.Total += item.Cost
		out.Items = append(out.Items, item)
	}
	return out, nil
}

func validateSettings(n Node, spec NodeSpec) error {
	d := n.Data
	switch n.Type {
	case TypeServer:
		if p := d.Pool; p != 0 && (p < spec.MinPool || p > spec.MaxPool) {
			return fmt.Errorf("connection pool must be between %d and %d", spec.MinPool, spec.MaxPool)
		}
	case TypeDatabase:
		if !slices.Contains([]string{"", "none", "sync", "async"}, d.Replication) {
			return fmt.Errorf("replication must be none, sync, or async")
		}
		if d.Partitions < 0 || d.Partitions > spec.MaxPartitions {
			return fmt.Errorf("partitions must be between 1 and %d", spec.MaxPartitions)
		}
	case TypeLoadBalancer:
		if !slices.Contains([]string{"", "round_robin", "least_connections"}, d.Algorithm) {
			return fmt.Errorf("algorithm must be round_robin or least_connections")
		}
	case TypeCache:
		if !slices.Contains([]string{"", "ttl", "invalidate"}, d.Policy) {
			return fmt.Errorf("cache policy must be ttl or invalidate")
		}
		if d.TTLMs < 0 || d.TTLMs > 3600000 {
			return fmt.Errorf("TTL must be at most an hour")
		}
	case TypeRateLimiter:
		if d.Limit < 0 || d.Limit > 100000 {
			return fmt.Errorf("limit must be at most 100,000 requests per second")
		}
	case TypeQueue:
		if d.Consumers < 0 || d.Consumers > spec.MaxConsumers {
			return fmt.Errorf("consumers must be between 1 and %d", spec.MaxConsumers)
		}
	case TypeLock:
		if d.LeaseMs < 0 || d.LeaseMs > 60000 {
			return fmt.Errorf("lease must be at most 60 seconds")
		}
	case TypeSchemaRegistry:
		if len(d.Fields) > 0 {
			if err := validateSchema(d.Fields); err != nil {
				return err
			}
		}
	}
	if len(d.Fields) > 0 && n.Type != TypeSchemaRegistry {
		return fmt.Errorf("only a schema registry has fields")
	}
	return nil
}

func joinComma(s []string) string {
	out := ""
	for i, x := range s {
		if i > 0 {
			out += ", "
		}
		out += x
	}
	return out
}
