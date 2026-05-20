<template>
  <div class="pipeline-progress">
    <div
      v-for="(stage, idx) in stages"
      :key="stage.agent"
      :class="['stage', `stage-${stage.status}`]"
    >
      <div class="stage-icon">
        <el-icon :size="20">
          <component :is="stage.icon" />
        </el-icon>
      </div>
      <div class="stage-label">{{ stage.label }}</div>
      <div v-if="idx < stages.length - 1" class="stage-arrow">
        <el-icon><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import type { DagNode } from '@/api/dag'

const props = defineProps<{
  nodes: DagNode[]
  currentAgent: string | null
}>()



interface Stage {
  agent: string
  label: string
  icon: string
  status: 'pending' | 'running' | 'completed' | 'failed'
}

const pipelineOrder = ['pm', 'architect', 'backend', 'frontend', 'qa', 'reviewer']

const stages = computed<Stage[]>(() => {
  const iconMap: Record<string, string> = {
    pm: 'Document',
    architect: 'SetUp',
    backend: 'Monitor',
    frontend: 'Platform',
    qa: 'Checked',
    reviewer: 'View',
  }
  const labelMap: Record<string, string> = {
    pm: 'PM',
    architect: 'Arch',
    backend: 'Backend',
    frontend: 'Frontend',
    qa: 'QA',
    reviewer: 'Review',
  }

  // 收集每种 agent 的状态
  const agentStatuses: Record<string, string> = {}
  for (const node of props.nodes) {
    const existing = agentStatuses[node.agent]
    if (!existing || node.status === 'running' || (node.status === 'failed' && existing !== 'running')) {
      agentStatuses[node.agent] = node.status
    }
  }

  // PM 始终作为第一阶段
  if (props.currentAgent === 'pm' || Object.keys(agentStatuses).length > 0) {
    agentStatuses['pm'] = agentStatuses['pm'] || 'completed'
  }

  return pipelineOrder
    .filter(agent => agentStatuses[agent] || agent === 'pm')
    .map(agent => ({
      agent,
      label: labelMap[agent] || agent,
      icon: iconMap[agent] || 'Document',
      status: (agentStatuses[agent] || 'pending') as Stage['status'],
    }))
})
</script>

<style scoped>
.pipeline-progress {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  overflow-x: auto;
}

.stage {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f0f0f0;
  white-space: nowrap;
  transition: all 0.3s;
}

.stage-completed {
  background: #f0f9eb;
  color: #67c23a;
}

.stage-running {
  background: #ecf5ff;
  color: #409eff;
  animation: pulse 1.5s infinite;
}

.stage-failed {
  background: #fef0f0;
  color: #f56c6c;
}

.stage-pending {
  background: #f4f4f5;
  color: #909399;
}

.stage-icon { display: flex; }
.stage-label { font-size: 12px; font-weight: 500; }
.stage-arrow { color: #c0c4cc; margin: 0 2px; display: flex; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
