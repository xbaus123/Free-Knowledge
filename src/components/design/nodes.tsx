import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { createContext, useContext } from "react";
import type { Frame, NodeSpec, SimNodeStats } from "../../lib/engine";

export type NodeKind = "client" | "loadBalancer" | "server" | "database";

/** A node's label and settings (serialized for the simulator). */
export type NodeData = {
  label: string;
  /** Server: connection pool size (requests served at once). */
  pool?: number;
  /** Database: replica mode. */
  replication?: "none" | "sync" | "async";
  /** Load balancer: how it picks a server. */
  algorithm?: "round_robin" | "least_connections";
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

export const NODE_META: Record<NodeKind, { name: string; accent: string; icon: React.ReactNode; hint: string }> = {
  client: {
    name: "Client",
    accent: "border-sky-500/60 text-sky-300",
    hint: "Your users. Sends the traffic.",
    icon: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
      </>
    ),
  },
  loadBalancer: {
    name: "Load Balancer",
    accent: "border-violet-500/60 text-violet-300",
    hint: "Spreads requests across servers and stops sending to ones that fail health checks.",
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
    hint: "Runs your API. Double-click to size its connection pool.",
    icon: (
      <>
        <rect x="3" y="4" width="18" height="7" rx="1.5" />
        <rect x="3" y="13" width="18" height="7" rx="1.5" />
        <path d="M7 7.5h.01M7 16.5h.01" />
      </>
    ),
  },
  database: {
    name: "Database",
    accent: "border-amber-500/60 text-amber-300",
    hint: "Stores data. Double-click to add a replica.",
    icon: (
      <>
        <ellipse cx="12" cy="5.5" rx="8" ry="2.5" />
        <path d="M4 5.5v13c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5v-13" />
        <path d="M4 12c0 1.4 3.6 2.5 8 2.5s8-1.1 8-2.5" />
      </>
    ),
  },
};

export function NodeIcon({ kind, className = "h-4 w-4" }: { kind: NodeKind; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      {NODE_META[kind].icon}
    </svg>
  );
}

/** A node's monthly cost under the catalog's prices. */
export function nodeCost(kind: NodeKind, data: NodeData, catalog?: Record<string, NodeSpec>): number {
  const spec = catalog?.[kind];
  if (!spec) return 0;
  let cost = spec.cost;
  if (kind === "server" && data.pool && data.pool > spec.workers) cost += (data.pool - spec.workers) * (spec.poolSlotCost ?? 0);
  if (kind === "database" && (data.replication === "sync" || data.replication === "async")) cost += spec.replicaCost ?? 0;
  return cost;
}

function settingsSummary(kind: NodeKind, data: NodeData): string | undefined {
  if (kind === "server" && data.pool) return `${data.pool}-connection pool`;
  if (kind === "database" && data.replication && data.replication !== "none") return `${data.replication} replica`;
  if (kind === "loadBalancer" && data.algorithm === "least_connections") return "least connections";
}

/** "hot" near capacity, "warm" when busy. */
export function heat(util: number, queue: number): "hot" | "warm" | undefined {
  if (util >= 0.9 || (queue > 0 && util >= 0.8)) return "hot";
  if (util >= 0.7) return "warm";
}

function SystemNode({ id, type, data, selected }: NodeProps<DesignNode>) {
  const kind = type as NodeKind;
  const meta = NODE_META[kind];
  const { stats, frame, problemNodes, chaosNodes, chaosMode, catalog } = useContext(SimulationContext);
  const total = stats?.[id];
  const live = frame?.nodes[id];
  const pool = kind === "server" ? (data.pool ?? catalog?.server?.workers) : kind === "database" ? catalog?.database?.workers : undefined;
  const util = live ? live.utilization : total?.utilization;
  const queue = live ? live.queue : (total?.maxQueue ?? 0);
  const hasLoad = kind === "server" || kind === "database";
  const temperature = hasLoad && util !== undefined ? heat(util, live?.queue ?? 0) : undefined;
  const down = !!live?.down;
  const doomed = chaosNodes.has(id);
  const problem = problemNodes.has(id) && !frame;
  const summary = settingsSummary(kind, data);
  const cost = catalog ? nodeCost(kind, data, catalog) : 0;

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
      title={chaosMode && kind !== "client" ? (doomed ? "Click to restore" : "Click to crash this node") : meta.hint}
      className={`relative w-44 rounded-lg border bg-zinc-900 px-3 py-2 shadow-lg transition-[box-shadow,opacity] ${ring} ${
        temperature === "hot" && !down ? "node-hot" : temperature === "warm" && !down ? "node-warm" : ""
      } ${chaosMode && kind !== "client" ? "cursor-crosshair hover:ring-2 hover:ring-red-500/50" : ""}`}
    >
      {kind !== "client" && <Handle type="target" position={Position.Left} className="!h-3 !w-3 !border-2 !border-zinc-900 !bg-zinc-400" />}
      <div className={`mb-0.5 flex items-center gap-1.5 text-[10px] font-medium tracking-wide uppercase ${meta.accent.split(" ")[1]}`}>
        <NodeIcon kind={kind} className="h-3.5 w-3.5" />
        {meta.name}
        {cost > 0 && <span className="ml-auto font-mono text-zinc-500 normal-case">${cost}</span>}
      </div>
      <div className="truncate text-sm font-medium text-zinc-100">{data.label}</div>
      {summary && <div className="truncate text-[11px] text-zinc-500">{summary}</div>}

      {(down || doomed) && (
        <span className="absolute -top-2 -right-2 rounded bg-red-600 px-1.5 py-0.5 text-[10px] font-bold text-white shadow">
          {down ? "DOWN" : "⚡ CHAOS"}
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
                pool {live.active}/{pool}
              </span>
              {live.queue > 0 && <span className="text-amber-400">queue {live.queue}</span>}
            </div>
          ) : (
            queue > 0 && <div className="mt-0.5">peak queue: {queue}</div>
          )}
        </div>
      )}
      {kind === "loadBalancer" && total && !frame && <div className="mt-1.5 text-[11px] text-zinc-400">{total.processed.toLocaleString()} requests</div>}

      {kind !== "database" && <Handle type="source" position={Position.Right} className="!h-3 !w-3 !border-2 !border-zinc-900 !bg-indigo-400" />}
    </div>
  );
}

function utilColor(u: number, kind: "text" | "bg") {
  const tone = u >= 0.9 ? "red" : u >= 0.7 ? "amber" : "emerald";
  return { red: { text: "text-red-400", bg: "bg-red-500" }, amber: { text: "text-amber-400", bg: "bg-amber-500" }, emerald: { text: "text-emerald-400", bg: "bg-emerald-500" } }[tone][kind];
}

export const nodeTypes = {
  client: SystemNode,
  loadBalancer: SystemNode,
  server: SystemNode,
  database: SystemNode,
};
