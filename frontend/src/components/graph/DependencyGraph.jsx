import { memo, useEffect, useMemo } from 'react'
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
import { FileCode2 } from 'lucide-react'

import '@xyflow/react/dist/style.css'
import './DependencyGraph.css'

const NODE_WIDTH = 228
const COLUMN_GAP = 96
const ROW_HEIGHT = 92

const FileNode = memo(({ data, selected }) => {
  const isDimmed = data.dimmed

  return (
    <div
      className={[
        'graph-file-node',
        selected ? 'selected' : '',
        isDimmed ? 'dimmed' : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <Handle type="target" position={Position.Left} />

      <div className="graph-file-node-top">
        <FileCode2 size={15} />
        <strong>{data.label}</strong>
      </div>

      <span className="graph-file-node-path">
        {data.file_path}
      </span>

      <div className="graph-file-node-meta">
        <span>{data.language}</span>
        <span>
          {data.outboundCount} out · {data.inboundCount} in
        </span>
      </div>

      <Handle type="source" position={Position.Right} />
    </div>
  )
})

FileNode.displayName = 'FileNode'

const nodeTypes = { file: FileNode }

function buildLayout(graph) {
  const groups = new Map()

  graph.nodes.forEach((node) => {
    const separator = node.file_path.lastIndexOf('/')
    const directory =
      separator === -1
        ? 'Project root'
        : node.file_path.slice(0, separator)

    if (!groups.has(directory)) {
      groups.set(directory, [])
    }

    groups.get(directory).push(node)
  })

  const inboundCounts = {}
  const outboundCounts = {}

  graph.edges.forEach((edge) => {
    outboundCounts[edge.source] =
      (outboundCounts[edge.source] || 0) + 1
    inboundCounts[edge.target] =
      (inboundCounts[edge.target] || 0) + 1
  })

  const directories = [...groups.keys()].sort()

  const nodes = []

  directories.forEach((directory, columnIndex) => {
    const directoryFiles = groups.get(directory)

    directoryFiles.sort((first, second) =>
      first.file_path.localeCompare(second.file_path)
    )

    directoryFiles.forEach((node, rowIndex) => {
      nodes.push({
        id: String(node.id),
        type: 'file',
        position: {
          x: columnIndex * (NODE_WIDTH + COLUMN_GAP),
          y: rowIndex * ROW_HEIGHT,
        },
        style: { width: NODE_WIDTH },
        data: {
          ...node,
          inboundCount: inboundCounts[node.id] || 0,
          outboundCount: outboundCounts[node.id] || 0,
          dimmed: false,
        },
      })
    })
  })

  return nodes
}

function DependencyGraph({
  graph,
  selectedNodeId,
  onSelectNode,
}) {
  const layoutNodes = useMemo(() => buildLayout(graph), [graph])

  const flowEdges = useMemo(
    () =>
      graph.edges.map((edge) => ({
        id: String(edge.id),
        source: String(edge.source),
        target: String(edge.target),
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#60a5fa',
          width: 18,
          height: 18,
        },
        style: {
          stroke: '#3b82f6',
          strokeWidth: 1.6,
        },
        data: edge,
      })),
    [graph.edges]
  )

  const [nodes, setNodes, onNodesChange] = useNodesState(layoutNodes)
  const [edges, setEdges, onEdgesChange] =
    useEdgesState(flowEdges)

  useEffect(() => {
    setNodes(layoutNodes)
    setEdges(flowEdges)
  }, [layoutNodes, flowEdges, setNodes, setEdges])

  return (
    <div className="dependency-graph">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onSelectNode(Number(node.id))}
        onPaneClick={() => onSelectNode(null)}
        fitView
        fitViewOptions={{ padding: 0.18 }}
        minZoom={0.05}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable
        className={selectedNodeId ? 'has-selection' : ''}
      >
        <Background color="#1b2a3f" gap={22} size={1} />
        <Controls showInteractive={false} />
        <MiniMap
          pannable
          zoomable
          nodeColor="#2f6dbb"
          maskColor="rgba(8, 13, 24, 0.75)"
        />
      </ReactFlow>
    </div>
  )
}

export default DependencyGraph
