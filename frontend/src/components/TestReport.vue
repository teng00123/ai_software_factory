<template>
  <div class="test-report">
    <div v-if="!tests" class="empty-text">{{ $t('dag.noArtifacts') }}</div>
    <template v-else>
      <!-- Summary Bar -->
      <div class="test-summary">
        <div class="summary-stat">
          <span class="stat-num stat-total">{{ tests.total }}</span>
          <span class="stat-label">Total</span>
        </div>
        <div class="summary-stat">
          <span class="stat-num stat-passed">{{ tests.passed }}</span>
          <span class="stat-label">Passed</span>
        </div>
        <div class="summary-stat">
          <span class="stat-num stat-failed">{{ tests.failed }}</span>
          <span class="stat-label">Failed</span>
        </div>
        <div class="summary-stat">
          <span class="stat-num stat-error">{{ tests.errors }}</span>
          <span class="stat-label">Errors</span>
        </div>
        <div class="progress-bar">
          <div class="progress-passed" :style="{ width: passRate + '%' }"></div>
        </div>
      </div>
      <!-- Results Table -->
      <el-table :data="tests.results" size="small" stripe>
        <el-table-column prop="test_name" label="Test" min-width="200" />
        <el-table-column prop="status" label="Status" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="Duration" width="100">
          <template #default="{ row }">{{ row.duration_ms }}ms</template>
        </el-table-column>
        <el-table-column prop="error_msg" label="Error" min-width="150" show-overflow-tooltip />
      </el-table>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TestSummary } from '@/api/review'

const props = defineProps<{ tests: TestSummary | null }>()

const passRate = computed(() => {
  if (!props.tests || props.tests.total === 0) return 0
  return Math.round((props.tests.passed / props.tests.total) * 100)
})

function statusType(status: string) {
  const map: Record<string, string> = { passed: 'success', failed: 'danger', error: 'danger', skipped: 'warning' }
  return map[status] || 'info'
}
</script>

<style scoped>
.test-report { padding: 0; }
.empty-text { text-align: center; color: #999; padding: 40px; }
.test-summary { display: flex; align-items: center; gap: 24px; margin-bottom: 16px; padding: 12px; background: #fafafa; border-radius: 4px; flex-wrap: wrap; }
.summary-stat { text-align: center; }
.stat-num { font-size: 24px; font-weight: bold; display: block; }
.stat-label { font-size: 12px; color: #909399; }
.stat-total { color: #303133; }
.stat-passed { color: #67c23a; }
.stat-failed { color: #f56c6c; }
.stat-error { color: #e6a23c; }
.progress-bar { flex: 1; height: 8px; background: #f56c6c; border-radius: 4px; overflow: hidden; min-width: 100px; }
.progress-passed { height: 100%; background: #67c23a; transition: width 0.3s; }
</style>
