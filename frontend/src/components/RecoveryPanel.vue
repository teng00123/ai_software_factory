<template>
  <div class="recovery-panel">
    <!-- Actions -->
    <div class="recovery-actions">
      <el-button
        type="warning"
        :loading="retrying"
        :disabled="!hasFailedNodes"
        @click="$emit('retryAll')"
      >
        <el-icon><RefreshRight /></el-icon>
        {{ retrying ? $t('recovery.retrying') : $t('recovery.retryAll') }}
      </el-button>
    </div>

    <!-- Error Logs -->
    <div class="section">
      <h4>{{ $t('recovery.errors') }}</h4>
      <div v-if="!errors.length" class="empty-text">{{ $t('recovery.noErrors') }}</div>
      <div v-else class="error-list">
        <div v-for="err in errors" :key="err.id" class="error-item">
          <div class="error-header">
            <el-tag :type="err.is_recoverable ? 'warning' : 'danger'" size="small">
              {{ err.is_recoverable ? $t('recovery.recoverable') : $t('recovery.notRecoverable') }}
            </el-tag>
            <el-tag size="small" type="info">{{ err.error_type || 'unknown' }}</el-tag>
            <span v-if="err.node_id" class="error-node">{{ err.node_id }}</span>
          </div>
          <div class="error-message">{{ err.error_message }}</div>
        </div>
      </div>
    </div>

    <!-- Retry History Timeline -->
    <div class="section">
      <h4>{{ $t('recovery.retries') }}</h4>
      <div v-if="!retries.length" class="empty-text">{{ $t('recovery.noRetries') }}</div>
      <el-timeline v-else>
        <el-timeline-item
          v-for="r in retries"
          :key="r.id"
          :type="r.status === 'success' ? 'success' : 'danger'"
          :hollow="r.status !== 'success'"
        >
          <div class="retry-item">
            <div class="retry-header">
              <el-tag :type="r.status === 'success' ? 'success' : 'danger'" size="small">
                {{ r.status }}
              </el-tag>
              <span class="retry-node">{{ r.node_id }}</span>
              <span class="retry-attempt">#{{ r.attempt }}</span>
            </div>
            <div class="retry-meta">
              <span v-if="r.strategy">{{ $t('recovery.strategy') }}: {{ r.strategy }}</span>
              <span v-if="r.model_used"> | Model: {{ r.model_used }}</span>
              <span> | {{ r.duration_ms }}ms</span>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RefreshRight } from '@element-plus/icons-vue'
import type { ErrorLogItem, RetryHistoryItem } from '@/api/recovery'
import type { DagNode } from '@/api/dag'

const props = defineProps<{
  errors: ErrorLogItem[]
  retries: RetryHistoryItem[]
  nodes: DagNode[]
  retrying: boolean
}>()

defineEmits<{
  retryAll: []
}>()

const hasFailedNodes = computed(() => props.nodes.some(n => n.status === 'failed'))
</script>

<style scoped>
.recovery-panel { padding: 0; }
.recovery-actions { margin-bottom: 16px; }
.section { margin-bottom: 20px; }
.section h4 { margin-bottom: 10px; color: #303133; }
.empty-text { color: #999; text-align: center; padding: 20px; font-size: 13px; }
.error-list { display: flex; flex-direction: column; gap: 10px; }
.error-item { padding: 10px; background: #fef0f0; border-radius: 4px; border-left: 3px solid #f56c6c; }
.error-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.error-node { font-family: monospace; font-size: 12px; color: #606266; }
.error-message { font-size: 13px; color: #303133; word-break: break-all; }
.retry-item { padding: 2px 0; }
.retry-header { display: flex; align-items: center; gap: 8px; }
.retry-node { font-family: monospace; font-size: 12px; }
.retry-attempt { font-size: 12px; color: #909399; }
.retry-meta { font-size: 12px; color: #909399; margin-top: 4px; }
</style>
