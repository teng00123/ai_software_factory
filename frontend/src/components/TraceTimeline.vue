<template>
  <div class="trace-timeline">
    <div v-if="!trace" class="empty-text">No trace data</div>
    <template v-else>
      <div class="trace-summary">
        <el-tag>Total: {{ trace.total_duration_ms }}ms</el-tag>
        <el-tag type="info">Tokens: {{ trace.total_tokens }}</el-tag>
        <el-tag type="warning">${{ trace.total_cost_usd.toFixed(4) }}</el-tag>
      </div>
      <div class="gantt">
        <div v-for="item in trace.trace" :key="item.node_id" class="gantt-row">
          <div class="gantt-label">
            <span class="gantt-agent">{{ item.agent }}</span>
            <span class="gantt-name">{{ item.label }}</span>
          </div>
          <div class="gantt-bar-container">
            <div
              :class="['gantt-bar', `gantt-${item.status}`]"
              :style="{ width: barWidth(item.duration_ms) + '%' }"
            >
              {{ item.duration_ms }}ms
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TaskTrace } from '@/api/metrics'

const props = defineProps<{ trace: TaskTrace | null }>()

const maxDuration = computed(() => {
  if (!props.trace) return 1
  return Math.max(...props.trace.trace.map(t => t.duration_ms), 1)
})

function barWidth(duration: number): number {
  return Math.max((duration / maxDuration.value) * 100, 5)
}
</script>

<style scoped>
.trace-timeline { padding: 0; }
.empty-text { text-align: center; color: #999; padding: 30px; }
.trace-summary { display: flex; gap: 8px; margin-bottom: 16px; }
.gantt { display: flex; flex-direction: column; gap: 8px; }
.gantt-row { display: flex; align-items: center; gap: 12px; }
.gantt-label { width: 160px; flex-shrink: 0; text-align: right; }
.gantt-agent { font-size: 11px; color: #909399; text-transform: uppercase; margin-right: 4px; }
.gantt-name { font-size: 12px; color: #606266; }
.gantt-bar-container { flex: 1; height: 24px; background: #f5f7fa; border-radius: 4px; overflow: hidden; }
.gantt-bar { height: 100%; border-radius: 4px; display: flex; align-items: center; padding: 0 8px; font-size: 11px; color: #fff; transition: width 0.3s; }
.gantt-completed { background: #67c23a; }
.gantt-failed { background: #f56c6c; }
.gantt-running { background: #409eff; }
.gantt-pending { background: #909399; }
</style>
