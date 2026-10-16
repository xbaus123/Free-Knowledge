import {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  Panel,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type IsValidConnection,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useEffect, useMemo, useRef, useState } from "react";
import * as engine from "../../lib/engine";
import { NodeProperties } from "./NodeProperties";
import { ALL_KINDS, NODE_META, NodeIcon, nodeCost, nodeTypes, SimulationContext, type DesignNode, type NodeData, type NodeKind } from "./nodes";

export interface DesignGraph {
  nodes: { id: string; type: NodeKind; position: { x: number; y: number }; data: NodeData }[];
  edges: { id: string; source: string; target: string }[];
}

interface Props {
  /** Diagram JSON ({nodes, edges}). Read once on mount; remount (change `key`) to load another. */
  initial: string;
  onChange: (json: string) => void;
  /** The last simulation, for totals and problem highlights. */
  result?: engine.SimResult;
  /** The replay frame to show (per-node load, per-edge traffic). */
  frame?: engine.Frame;
  /** Animates every connection while traffic is being simulated. */
  running?: boolean;
  /** Monthly budget to show against the diagram's cost. */
  budget?: number;
  /** Enables the chaos toolkit. */
  chaos?: engine.Chaos;
  onChaosChange?: (chaos: engine.Chaos) => void;
  /** The lesson's scenario: which node types to offer, and settings context. */
  scenario?: engine.SimulationConfig;
}

const DEFAULT_PALETTE: NodeKind[] = ["client", "loadBalancer", "server", "database"];
const NO_CHAOS: engine.Chaos = { nodes: [], edges: [] };

export function parseGraph(json: string): DesignGraph {
  try {
    const g = JSON.parse(json);
    return { nodes: Array.isArray(g?.nodes) ? g.nodes : [], edges: Array.isArray(g?.edges) ? g.edges : [] };
  } catch {
    return { nodes: [], edges: [] };
  }
}

/** Keeps only what defines the design, dropping React Flow's UI state. */
function serialize(nodes: DesignNode[], edges: Edge[]): string {
  const g: DesignGraph = {
    nodes: nodes.map((n) => {
      // Settings left at their defaults are undefined; leave them out.
      const data = Object.fromEntries(Object.entries(n.data).filter(([, v]) => v !== undefined)) as NodeData;
      return { id: n.id, type: n.type as NodeKind, position: { x: Math.round(n.position.x), y: Math.round(n.position.y) }, data };
    }),
    edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
  };
  return JSON.stringify(g);
}

function useCatalog() {
  const [catalog, setCatalog] = useState<Record<string, engine.NodeSpec>>();
  useEffect(() => {
    engine
      .simCatalog()
      .then((list) => setCatalog(Object.fromEntries(list.map((s) => [s.type, s]))))
      .catch(console.error);
  }, []);
  return catalog;
}

export function SystemCanvas(props: Props) {
  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  );
}

function Canvas({ initial, onChange, result, frame, running, budget, chaos = NO_CHAOS, onChaosChange, scenario }: Props) {
  const start = useMemo(() => parseGraph(initial), [initial]);
  const [nodes, setNodes, onNodesChange] = useNodesState<DesignNode>(start.nodes as DesignNode[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(start.edges);
  const { screenToFlowPosition } = useReactFlow();
  const wrapper = useRef<HTMLDivElement>(null);
  const catalog = useCatalog();
  const [editing, setEditing] = useState<string>();
  const [chaosMode, setChaosMode] = useState(false);

  // Report design changes (not selection or measuring) to the parent.
  const last = useRef(serialize(start.nodes as DesignNode[], start.edges));
  useEffect(() => {
    const json = serialize(nodes, edges);
    if (json !== last.current) {
      last.current = json;
      onChange(json);
    }
  }, [nodes, edges, onChange]);

  const onConnect = (c: Connection) => setEdges((es) => addEdge({ ...c, id: `${c.source}-${c.target}` }, es));

  // Traffic flows away from the client; some nodes only receive.
  const isValidConnection: IsValidConnection = (c) => {
    const source = nodes.find((n) => n.id === c.source);
    const target = nodes.find((n) => n.id === c.target);
    return (
      c.source !== c.target &&
      !!source &&
      !!target &&
      NODE_META[source.type as NodeKind]?.output &&
      NODE_META[target.type as NodeKind]?.input &&
      !edges.some((e) => e.source === c.source && e.target === c.target)
    );
  };
  const palette = ALL_KINDS.filter((k) => (scenario?.palette ?? DEFAULT_PALETTE).includes(k));

  const addNode = (kind: NodeKind) => {
    const count = nodes.filter((n) => n.type === kind).length;
    let n = count + 1;
    while (nodes.some((x) => x.id === `${kind}-${n}`)) n++;
    const label =
      kind === "server"
        ? `${scenario?.kind === "fencing" ? "Worker" : "API Server"} ${n}`
        : count === 0
          ? NODE_META[kind].name
          : `${NODE_META[kind].name} ${n}`;
    // Drop it in the first free spot near the middle of the visible canvas,
    // trying below then above so new nodes never land on existing ones.
    const box = wrapper.current?.getBoundingClientRect();
    const center = box ? screenToFlowPosition({ x: box.left + box.width / 2, y: box.top + box.height / 2 }) : { x: 0, y: 0 };
    const [w, h] = [200, 90]; // node footprint plus a gap
    const taken = (p: { x: number; y: number }) => nodes.some((o) => Math.abs(o.position.x - p.x) < w && Math.abs(o.position.y - p.y) < h);
    let position = { x: center.x - 88, y: center.y - 30 };
    for (let i = 1; i < 40 && taken(position); i++) {
      const step = Math.ceil(i / 2) * h * (i % 2 ? 1 : -1);
      position = { x: center.x - 88, y: center.y - 30 + step };
    }
    setNodes((ns) => [...ns.map((x) => ({ ...x, selected: false })), { id: `${kind}-${n}`, type: kind, position, data: { label }, selected: true }]);
  };

  const updateData = (id: string, data: NodeData) => setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, data } : n)));

  const toggle = (list: string[], id: string) => (list.includes(id) ? list.filter((x) => x !== id) : [...list, id]);
  const liveChaos = {
    nodes: chaos.nodes.filter((id) => nodes.some((n) => n.id === id)),
    edges: chaos.edges.filter((id) => edges.some((e) => e.id === id)),
  };
  const chaosCount = liveChaos.nodes.length + liveChaos.edges.length;

  const cost = catalog ? nodes.reduce((sum, n) => sum + nodeCost(n.type as NodeKind, n.data, catalog), 0) : undefined;
  const editingNode = nodes.find((n) => n.id === editing);

  const sim = useMemo(
    () => ({
      stats: result?.nodes,
      frame,
      problemNodes: new Set(result?.issues.map((i) => i.nodeId).filter((id): id is string => !!id)),
      chaosNodes: new Set(chaos.nodes),
      chaosMode,
      catalog,
    }),
    [result, frame, chaos.nodes, chaosMode, catalog],
  );

  // Connections: animated with traffic in the current frame, red and dashed when cut.
  // Arrowheads are sized in pixels so they don't balloon on thick, busy edges.
  const arrow = (color: string) => ({ type: MarkerType.ArrowClosed, width: 16, height: 16, markerUnits: "userSpaceOnUse", color });
  const styledEdges = edges.map((e) => {
    const cut = chaos.edges.includes(e.id);
    const traffic = frame?.edges[e.id] ?? 0;
    if (cut) {
      return {
        ...e,
        markerEnd: arrow("#ef4444"),
        animated: false,
        label: "✂ cut",
        labelStyle: { fill: "#fca5a5", fontSize: 11 },
        labelBgStyle: { fill: "#18181b" },
        style: { stroke: "#ef4444", strokeDasharray: "6 4", strokeWidth: 2 },
      };
    }
    if (frame) {
      return {
        ...e,
        markerEnd: arrow(traffic > 0 ? "#818cf8" : "#52525b"),
        animated: traffic > 0,
        style: traffic > 0 ? { stroke: "#818cf8", strokeWidth: 1.5 + Math.min(4, traffic / 6) } : { stroke: "#3f3f46", strokeWidth: 1.5 },
      };
    }
    return { ...e, markerEnd: arrow("#a1a1aa"), animated: !!running };
  });

  return (
    <SimulationContext.Provider value={sim}>
      <div ref={wrapper} className="h-full w-full">
        <ReactFlow
          nodes={nodes}
          edges={styledEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          isValidConnection={isValidConnection}
          onNodeDoubleClick={(_, n) => !chaosMode && setEditing(n.id)}
          onNodeClick={(_, n) => {
            if (chaosMode && onChaosChange && n.type !== "client" && n.type !== "schemaRegistry") onChaosChange({ ...liveChaos, nodes: toggle(liveChaos.nodes, n.id) });
          }}
          onEdgeClick={(_, e) => {
            if (chaosMode && onChaosChange) onChaosChange({ ...liveChaos, edges: toggle(liveChaos.edges, e.id) });
          }}
          onPaneClick={() => setEditing(undefined)}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={{ type: "smoothstep", style: { strokeWidth: 1.5 } }}
          colorMode="dark"
          fitView
          fitViewOptions={{ padding: 0.3, maxZoom: 1.1 }}
          deleteKeyCode={["Backspace", "Delete"]}
          zoomOnDoubleClick={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#3f3f46" />
          <Controls showInteractive={false} />
          <Panel position="top-left" className="flex flex-col gap-1 rounded-lg border border-zinc-800 bg-zinc-950/90 p-1.5 text-xs">
            <span className="px-1.5 pt-0.5 pb-1 text-[10px] font-medium tracking-wide text-zinc-500 uppercase">Add</span>
            {palette.map((kind) => (
              <button
                key={kind}
                onClick={() => addNode(kind)}
                title={NODE_META[kind].hint}
                className="flex items-center gap-2 rounded px-2 py-1.5 text-left text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
              >
                <span className={NODE_META[kind].accent.split(" ")[1]}>
                  <NodeIcon kind={kind} />
                </span>
                {NODE_META[kind].name}
                {catalog?.[kind]?.cost ? <span className="ml-auto pl-2 font-mono text-[10px] text-zinc-500">${catalog[kind].cost}</span> : null}
              </button>
            ))}
          </Panel>

          {onChaosChange && (
            <Panel position="top-center" className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950/90 p-1.5 text-xs whitespace-nowrap">
              <button
                onClick={() => {
                  setChaosMode((m) => !m);
                  setEditing(undefined);
                }}
                aria-pressed={chaosMode}
                title="Crash nodes or cut connections to see how your design copes"
                className={`rounded px-2.5 py-1 font-medium ${chaosMode ? "bg-red-600 text-white hover:bg-red-500" : "text-zinc-300 hover:bg-zinc-800"}`}
              >
                ⚡ Chaos{chaosMode ? ": on" : ""}
              </button>
              {chaosMode && <span className="hidden text-zinc-400 xl:inline">Click a node to crash it, or a connection to cut it.</span>}
              {chaosCount > 0 && (
                <button onClick={() => onChaosChange(NO_CHAOS)} className="rounded px-2 py-1 text-zinc-300 hover:bg-zinc-800">
                  Restore all ({chaosCount})
                </button>
              )}
            </Panel>
          )}

          {editingNode && (
            <Panel position="top-right">
              <NodeProperties
                node={editingNode}
                catalog={catalog}
                scenario={scenario}
                onChange={(data) => updateData(editingNode.id, data)}
                onClose={() => setEditing(undefined)}
              />
            </Panel>
          )}

          {cost !== undefined && (
            <Panel position="bottom-right" className="rounded-lg border border-zinc-800 bg-zinc-950/90 px-3 py-1.5 text-xs">
              <span className="text-zinc-400">Monthly cost </span>
              <span className={`font-mono ${budget && cost > budget ? "text-red-400" : "text-zinc-100"}`}>${cost}</span>
              {budget ? <span className="text-zinc-500"> / ${budget} budget</span> : null}
            </Panel>
          )}
        </ReactFlow>
      </div>
    </SimulationContext.Provider>
  );
}
