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
import { useEffect, useMemo, useRef } from "react";
import type { SimResult } from "../../lib/engine";
import { NODE_META, NodeIcon, nodeTypes, SimulationContext, type DesignNode, type NodeKind } from "./nodes";

export interface DesignGraph {
  nodes: { id: string; type: NodeKind; position: { x: number; y: number }; data: { label: string } }[];
  edges: { id: string; source: string; target: string }[];
}

interface Props {
  /** Diagram JSON ({nodes, edges}). Read once on mount; remount (change `key`) to load another. */
  initial: string;
  onChange: (json: string) => void;
  result?: SimResult;
  /** Animates connections while traffic is flowing. */
  running?: boolean;
}

const PALETTE: NodeKind[] = ["loadBalancer", "server", "database", "client"];

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
    nodes: nodes.map((n) => ({
      id: n.id,
      type: n.type as NodeKind,
      position: { x: Math.round(n.position.x), y: Math.round(n.position.y) },
      data: { label: n.data.label },
    })),
    edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
  };
  return JSON.stringify(g);
}

export function SystemCanvas(props: Props) {
  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  );
}

function Canvas({ initial, onChange, result, running }: Props) {
  const start = useMemo(() => parseGraph(initial), [initial]);
  const [nodes, setNodes, onNodesChange] = useNodesState<DesignNode>(start.nodes as DesignNode[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(start.edges);
  const { screenToFlowPosition } = useReactFlow();
  const wrapper = useRef<HTMLDivElement>(null);

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

  // Traffic flows away from the client and ends at databases.
  const isValidConnection: IsValidConnection = (c) => {
    const target = nodes.find((n) => n.id === c.target);
    return c.source !== c.target && target?.type !== "client" && !edges.some((e) => e.source === c.source && e.target === c.target);
  };

  const addNode = (kind: NodeKind) => {
    const count = nodes.filter((n) => n.type === kind).length;
    let n = count + 1;
    while (nodes.some((x) => x.id === `${kind}-${n}`)) n++;
    const label = kind === "server" ? `API Server ${n}` : count === 0 ? NODE_META[kind].name : `${NODE_META[kind].name} ${n}`;
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

  const sim = useMemo(
    () => ({ stats: result?.nodes, problemNodes: new Set(result?.issues.map((i) => i.nodeId).filter((id): id is string => !!id)) }),
    [result],
  );

  return (
    <SimulationContext.Provider value={sim}>
      <div ref={wrapper} className="h-full w-full">
        <ReactFlow
          nodes={nodes}
          edges={running ? edges.map((e) => ({ ...e, animated: true })) : edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          isValidConnection={isValidConnection}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={{ type: "smoothstep", markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 }, style: { strokeWidth: 1.5 } }}
          colorMode="dark"
          fitView
          fitViewOptions={{ padding: 0.3, maxZoom: 1.1 }}
          deleteKeyCode={["Backspace", "Delete"]}
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#3f3f46" />
          <Controls showInteractive={false} />
          <Panel position="top-left" className="flex flex-col gap-1 rounded-lg border border-zinc-800 bg-zinc-950/90 p-1.5 text-xs">
            <span className="px-1.5 pt-0.5 pb-1 text-[10px] font-medium tracking-wide text-zinc-500 uppercase">Add</span>
            {PALETTE.map((kind) => (
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
              </button>
            ))}
          </Panel>
        </ReactFlow>
      </div>
    </SimulationContext.Provider>
  );
}
