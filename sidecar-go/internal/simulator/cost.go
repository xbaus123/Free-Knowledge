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
	// Databases: a replica (sync or async) costs this much more.
	ReplicaCost int `json:"replicaCost,omitempty"`
}

// The catalog is tuned so one default server can't absorb the lessons'
// burst (4 workers / 6 ms ≈ 667 req/s against 1,000 req/s) but two can.
var catalog = map[string]NodeSpec{
	TypeClient:       {Type: TypeClient, Name: "Client"},
	TypeLoadBalancer: {Type: TypeLoadBalancer, Name: "Load Balancer", Cost: 20, ServiceMs: 1},
	TypeServer:       {Type: TypeServer, Name: "Server", Cost: 10, Workers: 4, ServiceMs: 6, MinPool: 1, MaxPool: 32, PoolSlotCost: 10},
	TypeDatabase:     {Type: TypeDatabase, Name: "Database", Cost: 50, Workers: 50, ServiceMs: 3, ReplicaCost: 40},
}

// Catalog lists the node types, for the canvas's palette and price tags.
func Catalog() []NodeSpec {
	out := []NodeSpec{}
	for _, t := range []string{TypeClient, TypeLoadBalancer, TypeServer, TypeDatabase} {
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
		item := CostItem{NodeID: n.ID, Label: n.Data.Label, Cost: spec.Cost}
		switch n.Type {
		case TypeServer:
			if p := n.Data.Pool; p != 0 {
				if p < spec.MinPool || p > spec.MaxPool {
					return out, fmt.Errorf("%s: connection pool must be between %d and %d", n.ID, spec.MinPool, spec.MaxPool)
				}
				if extra := p - spec.Workers; extra > 0 {
					item.Cost += extra * spec.PoolSlotCost
					item.Detail = fmt.Sprintf("%d-connection pool (+$%d)", p, extra*spec.PoolSlotCost)
				}
			}
		case TypeDatabase:
			if !slices.Contains([]string{"", "none", "sync", "async"}, n.Data.Replication) {
				return out, fmt.Errorf("%s: replication must be none, sync, or async", n.ID)
			}
			if r := n.Data.Replication; r == "sync" || r == "async" {
				item.Cost += spec.ReplicaCost
				item.Detail = fmt.Sprintf("%s replica (+$%d)", r, spec.ReplicaCost)
			}
		case TypeLoadBalancer:
			if !slices.Contains([]string{"", "round_robin", "least_connections"}, n.Data.Algorithm) {
				return out, fmt.Errorf("%s: algorithm must be round_robin or least_connections", n.ID)
			}
		}
		out.Total += item.Cost
		out.Items = append(out.Items, item)
	}
	return out, nil
}
