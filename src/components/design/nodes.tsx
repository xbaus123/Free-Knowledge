import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { createContext, useContext } from "react";
import type { Frame, NodeSpec, SchemaField, SimNodeStats } from "../../lib/engine";

export type NodeKind =
  | "client"
  | "cdn"
  | "rateLimiter"
  | "loadBalancer"
  | "server"
  | "cache"
  | "database"
  | "replica"
  | "queue"
  | "searchIndex"
  | "lock"
  | "schemaRegistry";

/** Every node type, in palette order. */
export const ALL_KINDS: NodeKind[] = [
  "client",
  "cdn",
  "rateLimiter",
  "loadBalancer",
  "server",
  "cache",
  "database",
  "replica",
  "queue",
  "searchIndex",
  "lock",
  "schemaRegistry",
];

/** A node's label and settings (serialized for the simulator). */
export type NodeData = {
  label: string;
  /** Server: connection pool size (requests served at once). */
  pool?: number;
  /** Server: app version it runs. */
  version?: string;
  /** Database: standby replica mode. */
  replication?: "none" | "sync" | "async";
  /** Database: number of partitions (shards). */
  partitions?: number;
  /** Database: publish committed changes to connected queues (change data capture). */
  outbox?: boolean;
  /** Database: reject writes with a fencing token older than one already seen. */
  checkTokens?: boolean;
  /** Load balancer: how it picks a server. */
  algorithm?: "round_robin" | "least_connections";
  /** Cache: entries expire after a TTL, or writes invalidate them. */
  policy?: "ttl" | "invalidate";
  ttlMs?: number;
  /** Rate limiter: requests per second allowed per user. */
  limit?: number;
  /** Queue: deliveries in flight to each subscriber. */
  consumers?: number;
  /** Lock service: lease length and fencing tokens. */
  leaseMs?: number;
  fencing?: boolean;
  /** Schema registry: the v2 schema. */
  fields?: SchemaField[];
};
export type DesignNode = Node<NodeData, NodeKind>;

/** Simulation state shown on the nodes, without touching the graph. */
export const SimulationContext = createContext<{
  stats?: Record<string, SimNodeStats>;
  /** The replay frame being shown, if any. */
  frame?: Frame;
  problemNodes: Set<string>;
  /** Nodes the chaos toolkit will crash. */
  chaosNodes: Set<string>;
  chaosMode: boolean;
  catalog?: Record<string, NodeSpec>;
}>({ problemNodes: new Set(), chaosNodes: new Set(), chaosMode: false });

interface Meta {
  name: string;
  /** Border and text color classes. */
  accent: string;
  icon: React.ReactNode;
  hint: string;
  /** Accepts incoming connections. */
  input: boolean;
  /** Sends requests onward. */
  output: boolean;
}

export const NODE_META: Record<NodeKind, Meta> = {
  client: {
    name: "Client",
    accent: "border-sky-500/60 text-sky-300",
    hint: "Your users. Sends the traffic.",
    input: false,
    output: true,
    icon: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
      </>
    ),
  },
  cdn: {
    name: "CDN",
    accent: "border-cyan-500/60 text-cyan-300",
    hint: "Caches images and scripts at the edge, close to users, and passes everything else on.",
    input: true,
    output: true,
    icon: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18" />
        <path d="M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z" />
      </>
    ),
  },
  rateLimiter: {
    name: "Rate Limiter",
    accent: "border-orange-500/60 text-orange-300",
    hint: "Caps how many requests each user may send per second. Double-click to set the limit.",
    input: true,
    output: true,
    icon: (
      <>
        <path d="M4 17a8 8 0 1 1 16 0" />
        <path d="M12 17l4-5" />
        <path d="M12 17h.01" />
      </>
    ),
  },
  loadBalancer: {
    name: "Load Balancer",
    accent: "border-violet-500/60 text-violet-300",
    hint: "Spreads requests across servers and stops sending to ones that fail health checks.",
    input: true,
    output: true,
    icon: (
      <>
        <path d="M3 12h6" />
        <path d="M9 12l6-6h6" />
        <path d="M9 12l6 6h6" />
        <path d="M15 12h6" />
      </>
    ),
  },
  server: {
    name: "Server",
    accent: "border-emerald-500/60 text-emerald-300",
    hint: "Runs your API. Sends reads to the nearest cache, replica, or database; writes to a queue or database. Double-click to size its connection pool.",
    input: true,
    output: true,
    icon: (
      <>
        <rect x="3" y="4" width="18" height="7" rx="1.5" />
        <rect x="3" y="13" width="18" height="7" rx="1.5" />
        <path d="M7 7.5h.01M7 16.5h.01" />
      </>
    ),
  },
  cache: {
    name: "Cache",
    accent: "border-fuchsia-500/60 text-fuchsia-300",
    hint: "An in-memory store like Redis. Answers reads it holds and loads misses from the store behind it. Double-click for its policy.",
    input: true,
    output: true,
    icon: <path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" />,
  },
  database: {
    name: "Database",
    accent: "border-amber-500/60 text-amber-300",
    hint: "Stores data. Double-click for a standby replica, partitions, and more.",
    input: true,
    output: true,
    icon: (
      <>
        <ellipse cx="12" cy="5.5" rx="8" ry="2.5" />
        <path d="M4 5.5v13c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5v-13" />
        <path d="M4 12c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5" />
      </>
    ),
  },
  replica: {
    name: "Read Replica",
    accent: "border-yellow-500/60 text-yellow-300",
    hint: "A read-only copy of a database. Connect the database to it; it trails the primary by about 50 ms.",
    input: true,
    output: false,
    icon: (
      <>
        <ellipse cx="10" cy="5.5" rx="6" ry="2" />
        <path d="M4 5.5v10c0 1.1 2.7 2 6 2" />
        <ellipse cx="15" cy="11" rx="5.5" ry="2" />
        <path d="M9.5 11v7.5c0 1.1 2.5 2 5.5 2s5.5-.9 5.5-2V11" />
      </>
    ),
  },
  queue: {
    name: "Message Queue",
    accent: "border-teal-500/60 text-teal-300",
    hint: "A durable log like Kafka. Acknowledges writes at once and delivers every message to each service it's connected to, retrying until it succeeds.",
    input: true,
    output: true,
    icon: (
      <>
        <rect x="3" y="5" width="18" height="4" rx="1" />
        <rect x="3" y="11" width="18" height="4" rx="1" />
        <rect x="3" y="17" width="12" height="3" rx="1" />
      </>
    ),
  },
  searchIndex: {
    name: "Search Index",
    accent: "border-lime-500/60 text-lime-300",
    hint: "A search engine like Elasticsearch. It must receive every change to stay in sync with the database.",
    input: true,
    output: false,
    icon: (
      <>
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="M15.5 15.5L21 21" />
      </>
    ),
  },
  lock: {
    name: "Lock Service",
    accent: "border-blue-500/60 text-blue-300",
    hint: "Grants a lease to one worker at a time, like ZooKeeper or etcd. Double-click for the lease length and fencing tokens.",
    input: true,
    output: false,
    icon: (
      <>
        <rect x="5" y="11" width="14" height="10" rx="2" />
        <path d="M8 11V8a4 4 0 0 1 8 0v3" />
      </>
    ),
  },
  schemaRegistry: {
    name: "Schema Registry",
    accent: "border-stone-400/60 text-stone-300",
    hint: "Holds the message schema each app version uses. Double-click to edit v2.",
    input: false,
    output: false,
    icon: (
      <>
        <path d="M6 3h9l4 4v14H6z" />
        <path d="M9 11h7M9 15h7M9 7h4" />
      </>
    ),
  },
};

export function NodeIcon({ kind, className = "h-4 w-4" }: { kind: NodeKind; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      {NODE_META[kind]?.icon}
    </svg>
  );
}

/** A node's monthly cost under the catalog's prices. */
export function nodeCost(kind: NodeKind, data: NodeData, catalog?: Record<string, NodeSpec>): number {
  const spec = catalog?.[kind];
  if (!spec) return 0;
  let cost = spec.cost;
  if (kind === "server" && data.pool && data.pool > spec.workers) cost += (data.pool - spec.workers) * (spec.poolSlotCost ?? 0);
  if (kind === "database") {
    const parts = Math.max(1, data.partitions ?? 1);
    cost = spec.cost * parts;
    if (data.replication === "sync" || data.replication === "async") cost += (spec.replicaCost ?? 0) * parts;
  }
  return cost;
}

function settingsSummary(kind: NodeKind, data: NodeData): string | undefined {
  const parts: string[] = [];
  switch (kind) {
    case "server":
      if (data.pool) parts.push(`${data.pool}-connection pool`);
      break;
    case "database":
      if (data.partitions && data.partitions > 1) parts.push(`${data.partitions} partitions`);
      if (data.replication && data.replication !== "none") parts.push(`${data.replication} standby`);
      if (data.outbox) parts.push("publishes changes");
      if (data.checkTokens) parts.push("checks tokens");
      break;
    case "loadBalancer":
      if (data.algorithm === "least_connections") parts.push("least connections");
      break;
    case "cache":
      parts.push(data.policy === "invalidate" ? "invalidate on write" : `TTL ${formatMs(data.ttlMs ?? 60000)}`);
      break;
    case "rateLimiter":
      parts.push(`${data.limit ?? 20} req/s per user`);
      break;
    case "queue":
      if (data.consumers) parts.push(`${data.consumers} consumers`);
      break;
    case "lock":
      parts.push(`${formatMs(data.leaseMs ?? 10000)} lease`);
      if (data.fencing) parts.push("fencing tokens");
      break;
  }
  return parts.join(" · ") || undefined;
}

export function formatMs(ms: number) {
  return ms >= 1000 ? `${+(ms / 1000).toFixed(1)} s` : `${ms} ms`;
}

/** "hot" near capacity, "warm" when busy. */
export function heat(util: number, queue: number): "hot" | "warm" | undefined {
  if (util >= 0.9 || (queue > 0 && util >= 0.8)) return "hot";
  if (util >= 0.7) return "warm";
}

const LOADED: NodeKind[] = ["server", "database", "cache", "replica", "searchIndex"];

function SystemNode({ id, type, data, selected }: NodeProps<DesignNode>) {
  const kind = type as NodeKind;
  const meta = NODE_META[kind] ?? NODE_META.server;
  const { stats, frame, problemNodes, chaosNodes, chaosMode, catalog } = useContext(SimulationContext);
  const total = stats?.[id];
  const live = frame?.nodes[id];
  const pool = kind === "server" ? (data.pool ?? catalog?.server?.workers) : kind === "database" ? catalog?.database?.workers : undefined;
  const util = live ? live.utilization : total?.utilization;
  const queue = live ? live.queue : (total?.maxQueue ?? 0);
  const hasLoad = LOADED.includes(kind);
  const temperature = hasLoad && util !== undefined ? heat(util, live?.queue ?? 0) : undefined;
  const down = !!live?.down;
  const doomed = chaosNodes.has(id);
  const problem = problemNodes.has(id) && !frame;
  const summary = settingsSummary(kind, data);
  const cost = catalog ? nodeCost(kind, data, catalog) : 0;
  const breakable = chaosMode && kind !== "client" && kind !== "schemaRegistry";

  const ring = down
    ? "border-zinc-700 opacity-50 grayscale"
    : problem
      ? "border-red-500 ring-2 ring-red-500/40"
      : doomed
        ? "border-red-500/70 border-dashed"
        : selected
          ? "border-indigo-400 ring-2 ring-indigo-500/30"
          : "border-zinc-700";

  return (
    <div
      title={breakable ? (doomed ? "Click to restore" : "Click to crash this node") : meta.hint}
      className={`relative rounded-lg border bg-zinc-900 px-3 py-2 shadow-lg transition-[box-shadow,opacity] ${kind === "schemaRegistry" ? "w-52" : "w-44"} ${ring} ${
        temperature === "hot" && !down ? "node-hot" : temperature === "warm" && !down ? "node-warm" : ""
      } ${breakable ? "cursor-crosshair hover:ring-2 hover:ring-red-500/50" : ""}`}
    >
      {meta.input && <Handle type="target" position={Position.Left} className="!h-3 !w-3 !border-2 !border-zinc-900 !bg-zinc-400" />}
      <div className={`mb-0.5 flex items-center gap-1.5 text-[10px] font-medium tracking-wide uppercase ${meta.accent.split(" ")[1]}`}>
        <NodeIcon kind={kind} className="h-3.5 w-3.5" />
        {meta.name}
        {cost > 0 && <span className="ml-auto font-mono text-zinc-500 normal-case">${cost}</span>}
      </div>
      <div className="flex items-center gap-1.5">
        <span className="truncate text-sm font-medium text-zinc-100">{data.label}</span>
        {live?.badge && (
          <span className="ml-auto shrink-0 rounded bg-zinc-800 px-1.5 py-0.5 font-mono text-[10px] text-zinc-200" title="State at this point in the replay">
            {live.badge}
          </span>
        )}
      </div>
      {summary && <div className="truncate text-[11px] text-zinc-500">{summary}</div>}

      {kind === "schemaRegistry" && <SchemaPreview fields={data.fields} />}

      {(down || doomed) && (
        <span className="absolute -top-2 -right-2 rounded bg-red-600 px-1.5 py-0.5 text-[10px] font-bold text-white shadow">
          {down ? (live?.badge === "paused" ? "PAUSED" : "DOWN") : "⚡ CHAOS"}
        </span>
      )}

      {hasLoad && util !== undefined && !down && (
        <div className="mt-1.5 text-[11px] text-zinc-400">
          <div className="mb-0.5 flex justify-between">
            <span>CPU</span>
            <span className={utilColor(util, "text")}>{Math.round(util * 100)}%</span>
          </div>
          <div className="h-1 overflow-hidden rounded-full bg-zinc-800">
            <div className={`h-full transition-[width] duration-150 ${utilColor(util, "bg")}`} style={{ width: `${Math.max(2, util * 100)}%` }} />
          </div>
          {live && pool ? (
            <div className="mt-0.5 flex justify-between">
              <span>
                busy {live.active}/{pool * (kind === "database" ? Math.max(1, data.partitions ?? 1) : 1)}
              </span>
              {live.queue > 0 && <span className="text-amber-400">queue {live.queue}</span>}
            </div>
          ) : (
            queue > 0 && <div className="mt-0.5">peak queue: {queue}</div>
          )}
        </div>
      )}
      {kind === "queue" && live && (
        <div className={`mt-1.5 text-[11px] ${live.queue > 0 ? "text-amber-400" : "text-zinc-400"}`}>backlog: {live.queue} messages</div>
      )}
      {(kind === "loadBalancer" || kind === "cdn" || kind === "rateLimiter") && total && !frame && (
        <div className="mt-1.5 text-[11px] text-zinc-400">{total.processed.toLocaleString()} requests</div>
      )}

      {meta.output && <Handle type="source" position={Position.Right} className="!h-3 !w-3 !border-2 !border-zinc-900 !bg-indigo-400" />}
    </div>
  );
}

function SchemaPreview({ fields }: { fields?: SchemaField[] }) {
  if (!fields?.length) return <div className="mt-1 text-[11px] text-zinc-500">v2 = v1 (no changes yet)</div>;
  return (
    <div className="mt-1.5 space-y-px font-mono text-[10px] text-zinc-400">
      <div className="text-zinc-500">v2 schema</div>
      {[...fields]
        .sort((a, b) => a.tag - b.tag)
        .slice(0, 6)
        .map((f) => (
          <div key={f.tag} className="flex gap-1.5">
            <span className="w-4 text-right text-zinc-600">{f.tag}</span>
            <span className="truncate text-zinc-300">{f.name}</span>
            <span className="ml-auto text-zinc-500">
              {f.type}
              {f.required ? "!" : "?"}
            </span>
          </div>
        ))}
      {fields.length > 6 && <div className="text-zinc-500">+{fields.length - 6} more</div>}
    </div>
  );
}

function utilColor(u: number, kind: "text" | "bg") {
  const tone = u >= 0.9 ? "red" : u >= 0.7 ? "amber" : "emerald";
  return { red: { text: "text-red-400", bg: "bg-red-500" }, amber: { text: "text-amber-400", bg: "bg-amber-500" }, emerald: { text: "text-emerald-400", bg: "bg-emerald-500" } }[tone][kind];
}

export const nodeTypes = Object.fromEntries(ALL_KINDS.map((k) => [k, SystemNode]));
