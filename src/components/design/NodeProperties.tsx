import type { NodeSpec, SchemaField, SimulationConfig } from "../../lib/engine";
import { formatMs, NODE_META, NodeIcon, nodeCost, type DesignNode, type NodeData, type NodeKind } from "./nodes";

interface Props {
  node: DesignNode;
  catalog?: Record<string, NodeSpec>;
  /** The lesson's scenario, to show only the settings that matter in it. */
  scenario?: SimulationConfig;
  onChange: (data: NodeData) => void;
  onClose: () => void;
}

const field = "w-full rounded border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm outline-none focus:border-indigo-500";
const help = "mt-1 block text-xs text-zinc-500";

/** Settings sidebar for one node; opens on double-click. */
export function NodeProperties({ node, catalog, scenario, onChange, onClose }: Props) {
  const kind = node.type as NodeKind;
  const data = node.data;
  const spec = catalog?.[kind];
  const set = (patch: Partial<NodeData>) => onChange({ ...data, ...patch });
  const fencingLesson = scenario?.kind === "fencing";
  const hasQueues = !scenario?.palette || scenario.palette.includes("queue");

  return (
    <div
      className={`max-h-[calc(100vh-12rem)] overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-950/95 p-4 text-sm shadow-2xl backdrop-blur ${kind === "schemaRegistry" ? "w-[26rem]" : "w-72"}`}
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

      {kind === "server" && spec && !fencingLesson && (
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
          <span className={help}>
            Requests served at once, each taking {spec.serviceMs} ms. Capacity ≈{" "}
            {Math.round(((data.pool ?? spec.workers) / spec.serviceMs) * 1000).toLocaleString()} req/s. Each slot past {spec.workers} costs $
            {spec.poolSlotCost}/month.
          </span>
        </label>
      )}
      {kind === "server" && fencingLesson && (
        <p className="mb-3 text-xs text-zinc-500">A worker: it takes the lock, then writes to storage every 50 ms while it believes it holds the lease.</p>
      )}

      {kind === "database" && spec && (
        <>
          {!fencingLesson && (
            <>
              <Choice
                legend="Standby replica"
                name={`replication-${node.id}`}
                value={data.replication ?? "none"}
                onChange={(v) => set({ replication: v === "none" ? undefined : (v as NodeData["replication"]) })}
                options={[
                  ["none", "None", "One copy. If it crashes, every request that needs it fails."],
                  ["sync", "Synchronous", `Each write waits for the standby (+4 ms). Fails over in 150 ms with no data lost. +$${spec.replicaCost}/month per partition.`],
                  ["async", "Asynchronous", `No extra latency, but the standby lags: recent writes are lost if the primary crashes. +$${spec.replicaCost}/month per partition.`],
                ]}
              />
              <label className="mb-3 block">
                <span className="mb-1 flex justify-between text-xs text-zinc-400">
                  Partitions
                  <span className="font-mono text-zinc-200">{data.partitions ?? 1}</span>
                </span>
                <input
                  type="range"
                  min={1}
                  max={spec.maxPartitions ?? 8}
                  value={data.partitions ?? 1}
                  onChange={(e) => {
                    const p = Number(e.target.value);
                    set({ partitions: p === 1 ? undefined : p });
                  }}
                  className="w-full accent-indigo-500"
                />
                <span className={help}>
                  Splits the data by key across {data.partitions ?? 1} machine{(data.partitions ?? 1) > 1 ? "s" : ""}, each with {spec.workers} connections ×{" "}
                  {spec.serviceMs} ms ≈ {Math.round((spec.workers / spec.serviceMs) * 1000).toLocaleString()} queries/s. Each costs ${spec.cost}/month. One
                  hot key still lands on a single partition.
                </span>
              </label>
            </>
          )}
          {hasQueues && !fencingLesson && (
            <Toggle
              checked={!!data.outbox}
              onChange={(outbox) => set({ outbox: outbox || undefined })}
              label="Publish changes (outbox / CDC)"
              help="After each commit, send the change to every message queue this database connects to. Draw an edge from the database to the queue."
            />
          )}
          {fencingLesson && (
            <Toggle
              checked={!!data.checkTokens}
              onChange={(checkTokens) => set({ checkTokens: checkTokens || undefined })}
              label="Reject stale fencing tokens"
              help="Remember the highest token seen, and refuse any write that carries a lower one."
            />
          )}
        </>
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
          <span className={help}>Least connections helps when servers have different capacities.</span>
        </label>
      )}

      {kind === "cache" && (
        <>
          <Choice
            legend="When the data changes"
            name={`policy-${node.id}`}
            value={data.policy ?? "ttl"}
            onChange={(v) => set({ policy: v === "ttl" ? undefined : (v as NodeData["policy"]) })}
            options={[
              ["ttl", "Expire after a TTL", "Writes pass through untouched; cached copies stay until they expire. Simple, but readers see old data meanwhile."],
              ["invalidate", "Invalidate on write", "Writes that pass through this cache delete the cached copy, so the next read loads the new value."],
            ]}
          />
          {(data.policy ?? "ttl") === "ttl" && (
            <label className="mb-3 block">
              <span className="mb-1 block text-xs text-zinc-400">TTL</span>
              <select value={data.ttlMs ?? 60000} onChange={(e) => set({ ttlMs: Number(e.target.value) === 60000 ? undefined : Number(e.target.value) })} className={field}>
                {[100, 500, 1000, 5000, 60000].map((ms) => (
                  <option key={ms} value={ms}>
                    {formatMs(ms)}
                  </option>
                ))}
              </select>
            </label>
          )}
          <p className={help}>Reads go to the cache first; misses load from the replica or database it connects to. Message queues connected to it can also invalidate entries.</p>
        </>
      )}

      {kind === "rateLimiter" && spec && (
        <label className="mb-3 block">
          <span className="mb-1 block text-xs text-zinc-400">Requests per second, per user</span>
          <input
            type="number"
            min={1}
            max={100000}
            value={data.limit ?? spec.defaultLimit ?? 20}
            onChange={(e) => {
              const v = Math.max(1, Math.min(100000, Math.round(Number(e.target.value) || 1)));
              set({ limit: v === spec.defaultLimit ? undefined : v });
            }}
            className={field}
          />
          <span className={help}>A token bucket per user: short bursts up to the limit are fine; anything faster gets a 429. Set it too low and real users are turned away.</span>
        </label>
      )}

      {kind === "queue" && spec && (
        <label className="mb-3 block">
          <span className="mb-1 flex justify-between text-xs text-zinc-400">
            Consumers
            <span className="font-mono text-zinc-200">{data.consumers ?? spec.defaultConsumers}</span>
          </span>
          <input
            type="range"
            min={1}
            max={spec.maxConsumers ?? 32}
            value={data.consumers ?? spec.defaultConsumers ?? 4}
            onChange={(e) => {
              const c = Number(e.target.value);
              set({ consumers: c === spec.defaultConsumers ? undefined : c });
            }}
            className="w-full accent-indigo-500"
          />
          <span className={help}>
            Messages delivered in parallel to each connected service. Throughput ≈ consumers ÷ the time each message takes downstream. Writes are acknowledged as soon as
            they're queued.
          </span>
        </label>
      )}

      {kind === "lock" && spec && (
        <>
          <label className="mb-3 block">
            <span className="mb-1 block text-xs text-zinc-400">Lease length</span>
            <select value={data.leaseMs ?? spec.defaultLeaseMs} onChange={(e) => set({ leaseMs: Number(e.target.value) })} className={field}>
              {[500, 1000, 2000, 5000, 10000].map((ms) => (
                <option key={ms} value={ms}>
                  {formatMs(ms)}
                </option>
              ))}
            </select>
            <span className={help}>The holder renews every third of the lease. If it goes silent, the lock frees up when the lease runs out.</span>
          </label>
          <Toggle
            checked={!!data.fencing}
            onChange={(fencing) => set({ fencing: fencing || undefined })}
            label="Issue fencing tokens"
            help="Every grant comes with a number one higher than the last. Workers send it with each write."
          />
        </>
      )}

      {kind === "replica" && <p className="mb-3 text-xs text-zinc-500">Draw an edge from a database to this replica to replicate it. Servers and caches send reads here before the primary.</p>}
      {kind === "searchIndex" && (
        <p className="mb-3 text-xs text-zinc-500">
          Servers connected to it write each change here after the database commits (a dual write). A message queue connected to it delivers changes with retries instead.
        </p>
      )}
      {kind === "cdn" && <p className="mb-3 text-xs text-zinc-500">Put it between the Client and the rest of your system. It serves static files from the edge after the first request.</p>}

      {kind === "schemaRegistry" && <SchemaEditor v1={scenario?.schema?.v1 ?? []} fields={data.fields} onChange={(fields) => set({ fields })} />}

      {spec && spec.cost > 0 && (
        <div className="flex justify-between border-t border-zinc-800 pt-3 text-xs">
          <span className="text-zinc-400">Monthly cost</span>
          <span className="font-mono text-zinc-100">${nodeCost(kind, data, catalog)}</span>
        </div>
      )}
    </div>
  );
}

function Choice({
  legend,
  name,
  value,
  options,
  onChange,
}: {
  legend: string;
  name: string;
  value: string;
  options: readonly (readonly [string, string, string])[];
  onChange: (v: string) => void;
}) {
  return (
    <fieldset className="mb-3">
      <legend className="mb-1 text-xs text-zinc-400">{legend}</legend>
      {options.map(([v, label, text]) => (
        <label key={v} className="mb-1.5 flex cursor-pointer gap-2 rounded border border-zinc-800 p-2 hover:border-zinc-700">
          <input type="radio" name={name} checked={value === v} onChange={() => onChange(v)} className="mt-0.5 accent-indigo-500" />
          <span>
            <span className="block text-zinc-200">{label}</span>
            <span className="block text-xs text-zinc-500">{text}</span>
          </span>
        </label>
      ))}
    </fieldset>
  );
}

function Toggle({ checked, onChange, label, help: text }: { checked: boolean; onChange: (v: boolean) => void; label: string; help: string }) {
  return (
    <label className="mb-3 flex cursor-pointer gap-2 rounded border border-zinc-800 p-2 hover:border-zinc-700">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="mt-0.5 accent-indigo-500" />
      <span>
        <span className="block text-zinc-200">{label}</span>
        <span className="block text-xs text-zinc-500">{text}</span>
      </span>
    </label>
  );
}

const TYPES: SchemaField["type"][] = ["int64", "string", "bool"];

/** Edits the v2 schema beside the fixed v1 one. */
function SchemaEditor({ v1, fields, onChange }: { v1: SchemaField[]; fields?: SchemaField[]; onChange: (f: SchemaField[]) => void }) {
  const v2 = fields?.length ? fields : v1;
  const update = (i: number, patch: Partial<SchemaField>) => onChange(v2.map((f, j) => (j === i ? { ...f, ...patch } : f)));
  const remove = (i: number) => onChange(v2.filter((_, j) => j !== i));
  const add = () => {
    const tag = Math.max(0, ...v2.map((f) => f.tag), ...v1.map((f) => f.tag)) + 1;
    onChange([...v2, { tag, name: `field_${tag}`, type: "string" }]);
  };
  const tagCount = (tag: number) => v2.filter((f) => f.tag === tag).length;

  return (
    <div className="mb-3 space-y-3 text-xs">
      <div>
        <div className="mb-1 text-zinc-400">v1 (already deployed, can't change)</div>
        <table className="w-full font-mono">
          <tbody>
            {v1.map((f) => (
              <tr key={f.tag} className="text-zinc-500">
                <td className="w-8 py-0.5">{f.tag}</td>
                <td>{f.name}</td>
                <td>{f.type}</td>
                <td className="text-right">{f.required ? "required" : "optional"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <div className="mb-1 text-zinc-400">v2 (the version being rolled out)</div>
        <table className="w-full">
          <thead className="text-left text-[10px] text-zinc-500 uppercase">
            <tr>
              <th className="pb-1 font-normal">Tag</th>
              <th className="pb-1 font-normal">Name</th>
              <th className="pb-1 font-normal">Type</th>
              <th className="pb-1 font-normal">Req.</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {v2.map((f, i) => (
              <tr key={i}>
                <td className="w-14 pr-1 pb-1">
                  <input
                    type="number"
                    min={1}
                    max={99}
                    value={f.tag}
                    aria-label={`Tag of ${f.name}`}
                    onChange={(e) => update(i, { tag: Math.max(1, Math.min(99, Math.round(Number(e.target.value) || 1))) })}
                    className={`${field} px-1.5 py-1 font-mono text-xs ${tagCount(f.tag) > 1 ? "border-red-500" : ""}`}
                  />
                </td>
                <td className="pr-1 pb-1">
                  <input
                    value={f.name}
                    aria-label={`Name of field ${f.tag}`}
                    onChange={(e) => update(i, { name: e.target.value.replace(/[^A-Za-z0-9_]/g, "").slice(0, 40) })}
                    className={`${field} px-1.5 py-1 font-mono text-xs`}
                  />
                </td>
                <td className="pr-1 pb-1">
                  <select
                    value={f.type}
                    aria-label={`Type of ${f.name}`}
                    onChange={(e) => update(i, { type: e.target.value as SchemaField["type"] })}
                    className={`${field} px-1 py-1 text-xs`}
                  >
                    {TYPES.map((t) => (
                      <option key={t}>{t}</option>
                    ))}
                  </select>
                </td>
                <td className="pb-1 text-center">
                  <input
                    type="checkbox"
                    checked={!!f.required}
                    aria-label={`${f.name} is required`}
                    onChange={(e) => update(i, { required: e.target.checked || undefined })}
                    className="accent-indigo-500"
                  />
                </td>
                <td className="pb-1 pl-1">
                  <button onClick={() => remove(i)} aria-label={`Remove ${f.name}`} disabled={v2.length <= 1} className="rounded px-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200 disabled:opacity-40">
                    ✕
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <button onClick={add} disabled={v2.length >= 20} className="mt-1 rounded border border-zinc-700 px-2 py-1 text-zinc-300 hover:bg-zinc-800 disabled:opacity-40">
          + Add field
        </button>
        {v2.some((f) => tagCount(f.tag) > 1) && <p className="mt-1 text-red-400">Two fields can't share a tag.</p>}
      </div>
      <p className="text-zinc-500">
        Readers match fields by <span className="text-zinc-300">tag</span>. They skip tags they don't know, and use a default for optional fields that are missing. A missing
        required field, or a tag whose type or meaning changed, breaks decoding.
      </p>
    </div>
  );
}
