<template>
  <div class="dag-view">
    <div v-if="!nodes.length" class="empty-state">
      {{ $t('dag.noNodes') }}
    </div>
    <VueFlow
      v-else
      :nodes="flowNodes"
      :edges="flowEdges"
      :default-viewport="{ zoom: 0.9, x: 50, y: 50 }"
      fit-view-on-init
      class="flow-container"
    >
      <Background />
      <Controls />
      <template #node-custom="{ data }">
        <div :class="['dag-node', `dag-node-${data.status}`, `dag-agent-${data.agent}`]" @click="$emit('nodeClick', data)">
          <div class="node-agent">{{ data.agent }}</div>
          <div class="node-label">{{ data.label }}</div>
          <div class="node-status">
            <span class="status-dot"></span>
            {{ data.statusText }}
          </div>
        </div>
      </template>
    </VueFlow>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import { useI18n } from 'vue-i18n'
import type { DagNode, DagEdge } from '@/api/dag'

const props = defineProps<{
  nodes: DagNode[]
  edges: DagEdge[]
}>()

defineEmits<{
  nodeClick: [node: DagNode]
}>()

const { t } = useI18n()

const statusTextMap = computed(() => ({
  pending: t('tasks.status.pending'),
  running: t('tasks.status.running'),
  completed: t('tasks.status.completed'),
  failed: t('tasks.status.failed'),
}))

// 计算节点位置（简单的分层布局）
const flowNodes = computed(() => {
  // 按依赖层级分配 y 坐标
  const layers = computeLayers(props.nodes)
  const nodePositions: Record<string, { x: number; y: number }> = {}

  layers.forEach((layer, layerIdx) => {
    layer.forEach((node, nodeIdx) => {
      const x = 50 + nodeIdx * 250
      const y = 50 + layerIdx * 150
      nodePositions[node.node_id] = { x, y }
    })
  })

  return props.nodes.map((node) => ({
    id: node.node_id,
    type: 'custom',
    position: nodePositions[node.node_id] || { x: 0, y: 0 },
    data: {
      ...node,
      statusText: statusTextMap.value[node.status] || node.status,
    },
  }))
})

const flowEdges = computed(() => {
  return props.edges.map((edge, idx) => ({
    id: `e-${idx}`,
    source: edge.source,
    target: edge.target,
    animated: props.nodes.find(n => n.node_id === edge.target)?.status === 'running',
    style: { stroke: '#409eff' },
  }))
})

function computeLayers(nodes: DagNode[]): DagNode[][] {
  const nodeMap = new Map(nodes.map(n => [n.node_id, n]))
  const inDegree = new Map(nodes.map(n => [n.node_id, 0]))
  const adj = new Map<string, string[]>(nodes.map(n => [n.node_id, []]))

  for (const node of nodes) {
    const deps = node.depends_on || []
    for (const dep of deps) {
      if (adj.has(dep)) {
        adj.get(dep)!.push(node.node_id)
        inDegree.set(node.node_id, (inDegree.get(node.node_id) || 0) + 1)
      }
    }
  }

  const layers: DagNode[][] = []
  let queue = nodes.filter(n => (inDegree.get(n.node_id) || 0) === 0)

  while (queue.length > 0) {
    layers.push(queue)
    const nextQueue: DagNode[] = []
    for (const node of queue) {
      for (const neighbor of (adj.get(node.node_id) || [])) {
        inDegree.set(neighbor, (inDegree.get(neighbor) || 0) - 1)
        if (inDegree.get(neighbor) === 0) {
          const n = nodeMap.get(neighbor)
          if (n) nextQueue.push(n)
        }
      }
    }
    queue = nextQueue
  }

  return layers
}
</script>

<style scoped>
.dag-view {
  width: 100%;
  height: 400px;
  border: 1px solid #eee;
  border-radius: 4px;
  overflow: hidden;
}

.flow-container {
  width: 100%;
  height: 100%;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.dag-node {
  padding: 12px 16px;
  border-radius: 8px;
  border: 2px solid #ddd;
  background: #fff;
  min-width: 160px;
  cursor: pointer;
  transition: all 0.3s;
}

.dag-node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dag-node-pending {
  border-color: #909399;
}

.dag-node-running {
  border-color: #409eff;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.3);
}

.dag-node-completed {
  border-color: #67c23a;
}

.dag-node-failed {
  border-color: #f56c6c;
}

.node-agent {
  font-size: 11px;
  color: #909399;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.node-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 6px;
}

.node-status {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.dag-node-pending .status-dot {
  background: #909399;
}

.dag-node-running .status-dot {
  background: #409eff;
  animation: pulse 1.5s infinite;
}

.dag-node-completed .status-dot {
  background: #67c23a;
}

.dag-node-failed .status-dot {
  background: #f56c6c;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Agent type colors (top border accent) */
.dag-agent-pm .node-agent { color: #e6a23c; }
.dag-agent-architect .node-agent { color: #9b59b6; }
.dag-agent-backend .node-agent { color: #409eff; }
.dag-agent-frontend .node-agent { color: #67c23a; }
.dag-agent-qa .node-agent { color: #f56c6c; }
.dag-agent-reviewer .node-agent { color: #e91e63; }
</style>
