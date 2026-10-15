import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { createContext, useContext } from "react";
import type { SimNodeStats } from "../../lib/engine";

export type NodeKind = "client" | "loadBalancer" | "server" | "database";
export type DesignNode = Node<{ label: string }, NodeKind>;

/** Latest simulation results, shown on the nodes without touching the graph. */
export const SimulationContext = createContext<{ stats?: Record<string, SimNodeStats>; problemNodes: Set<string> }>({
  problemNodes: new Set(),
});

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
    hint: "Spreads requests across servers, round-robin.",
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
    hint: "Runs your API: 4 workers, 6 ms per request.",
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
    hint: "Stores data: 50 connections, 3 ms per query.",
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

function SystemNode({ id, type, data, selected }: NodeProps<DesignNode>) {
  const kind = type as NodeKind;
  const meta = NODE_META[kind];
  const { stats, problemNodes } = useContext(SimulationContext);
  const s = stats?.[id];
  const problem = problemNodes.has(id);
  const util = s && kind !== "client" && kind !== "loadBalancer" ? s.utilization : undefined;

  return (
    <div
      title={meta.hint}
      className={`w-44 rounded-lg border bg-zinc-900 px-3 py-2 shadow-lg transition-shadow ${
        problem ? "border-red-500 ring-2 ring-red-500/40" : selected ? "border-indigo-400 ring-2 ring-indigo-500/30" : "border-zinc-700"
      }`}
    >
      {kind !== "client" && <Handle type="target" position={Position.Left} className="!h-3 !w-3 !border-2 !border-zinc-900 !bg-zinc-400" />}
      <div className={`mb-0.5 flex items-center gap-1.5 text-[10px] font-medium tracking-wide uppercase ${meta.accent.split(" ")[1]}`}>
        <NodeIcon kind={kind} className="h-3.5 w-3.5" />
        {meta.name}
      </div>
      <div className="truncate text-sm font-medium text-zinc-100">{data.label}</div>

      {s && (
        <div className="mt-1.5 text-[11px] text-zinc-400">
          {util !== undefined ? (
            <>
              <div className="mb-0.5 flex justify-between">
                <span>CPU</span>
                <span className={utilColor(util, "text")}>{Math.round(util * 100)}%</span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-zinc-800">
                <div className={`h-full ${utilColor(util, "bg")}`} style={{ width: `${Math.max(2, util * 100)}%` }} />
              </div>
              {s.maxQueue > 0 && <div className="mt-0.5">peak queue: {s.maxQueue}</div>}
            </>
          ) : (
            kind !== "client" && <span>{s.processed.toLocaleString()} requests</span>
          )}
        </div>
      )}

      {kind !== "database" && <Handle type="source" position={Position.Right} className="!h-3 !w-3 !border-2 !border-zinc-900 !bg-indigo-400" />}
    </div>
  );
}

function utilColor(u: number, kind: "text" | "bg") {
  const tone = u >= 0.95 ? "red" : u >= 0.7 ? "amber" : "emerald";
  return { red: { text: "text-red-400", bg: "bg-red-500" }, amber: { text: "text-amber-400", bg: "bg-amber-500" }, emerald: { text: "text-emerald-400", bg: "bg-emerald-500" } }[tone][kind];
}

export const nodeTypes = {
  client: SystemNode,
  loadBalancer: SystemNode,
  server: SystemNode,
  database: SystemNode,
};
