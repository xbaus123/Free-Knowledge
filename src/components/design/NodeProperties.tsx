import type { NodeSpec } from "../../lib/engine";
import { NODE_META, NodeIcon, nodeCost, type DesignNode, type NodeData, type NodeKind } from "./nodes";

interface Props {
  node: DesignNode;
  catalog?: Record<string, NodeSpec>;
  onChange: (data: NodeData) => void;
  onClose: () => void;
}

const field = "w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm outline-none focus:border-indigo-500";

/** Settings sidebar for one node; opens on double-click. */
export function NodeProperties({ node, catalog, onChange, onClose }: Props) {
  const kind = node.type as NodeKind;
  const data = node.data;
  const spec = catalog?.[kind];
  const set = (patch: Partial<NodeData>) => onChange({ ...data, ...patch });

  return (
    <div
      className="w-72 rounded-lg border border-zinc-800 bg-zinc-950/95 p-4 text-sm shadow-2xl backdrop-blur"
      // Keep typing and clicks here from reaching the canvas (Backspace would delete the node).
      onKeyDown={(e) => e.stopPropagation()}
    >
      <div className="mb-3 flex items-center gap-2">
        <span className={NODE_META[kind].accent.split(" ")[1]}>
          <NodeIcon kind={kind} />
        </span>
        <h3 className="font-medium">{NODE_META[kind].name} settings</h3>
        <button onClick={onClose} aria-label="Close settings" className="ml-auto rounded px-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100">
          ✕
        </button>
      </div>

      <label className="mb-3 block">
        <span className="mb-1 block text-xs text-zinc-400">Name</span>
        <input value={data.label} onChange={(e) => set({ label: e.target.value })} className={field} />
      </label>

      {kind === "server" && spec && (
        <label className="mb-3 block">
          <span className="mb-1 flex justify-between text-xs text-zinc-400">
            Connection pool
            <span className="font-mono text-zinc-200">{data.pool ?? spec.workers}</span>
          </span>
          <input
            type="range"
            min={spec.minPool}
            max={spec.maxPool}
            value={data.pool ?? spec.workers}
            onChange={(e) => {
              const pool = Number(e.target.value);
              set({ pool: pool === spec.workers ? undefined : pool });
            }}
            className="w-full accent-indigo-500"
          />
          <span className="mt-1 block text-xs text-zinc-500">
            Requests served at once, each taking {spec.serviceMs} ms. Capacity ≈{" "}
            {Math.round(((data.pool ?? spec.workers) / spec.serviceMs) * 1000).toLocaleString()} req/s. Each slot past {spec.workers} costs $
            {spec.poolSlotCost}/month.
          </span>
        </label>
      )}

      {kind === "database" && spec && (
        <fieldset className="mb-3">
          <legend className="mb-1 text-xs text-zinc-400">Replication</legend>
          {(
            [
              ["none", "None", "One copy. If it crashes, every request that needs it fails."],
              ["sync", "Synchronous", `Each write waits for the replica (+4 ms per request). Fails over with no data lost. +$${spec.replicaCost}/month.`],
              ["async", "Asynchronous", `No extra latency, but the replica lags: recent writes are lost if the primary crashes. +$${spec.replicaCost}/month.`],
            ] as const
          ).map(([value, label, help]) => (
            <label key={value} className="mb-1.5 flex cursor-pointer gap-2 rounded border border-zinc-800 p-2 hover:border-zinc-700">
              <input
                type="radio"
                name={`replication-${node.id}`}
                checked={(data.replication ?? "none") === value}
                onChange={() => set({ replication: value === "none" ? undefined : value })}
                className="mt-0.5 accent-indigo-500"
              />
              <span>
                <span className="block text-zinc-200">{label}</span>
                <span className="block text-xs text-zinc-500">{help}</span>
              </span>
            </label>
          ))}
        </fieldset>
      )}

      {kind === "loadBalancer" && (
        <label className="mb-3 block">
          <span className="mb-1 block text-xs text-zinc-400">Algorithm</span>
          <select
            value={data.algorithm ?? "round_robin"}
            onChange={(e) => set({ algorithm: e.target.value === "round_robin" ? undefined : (e.target.value as NodeData["algorithm"]) })}
            className={field}
          >
            <option value="round_robin">Round robin: take turns</option>
            <option value="least_connections">Least connections: pick the least busy</option>
          </select>
          <span className="mt-1 block text-xs text-zinc-500">Least connections helps when servers have different capacities.</span>
        </label>
      )}

      {spec && (
        <div className="flex justify-between border-t border-zinc-800 pt-3 text-xs">
          <span className="text-zinc-400">Monthly cost</span>
          <span className="font-mono text-zinc-100">${nodeCost(kind, data, catalog)}</span>
        </div>
      )}
    </div>
  );
}
