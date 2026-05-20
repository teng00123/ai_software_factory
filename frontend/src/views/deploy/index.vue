<template>
  <div class="deploy-page">
    <div class="page-header">
      <h2 class="page-title">{{ $t('deploy.title') }}</h2>
    </div>

    <!-- Deployment List -->
    <el-card shadow="never">
      <div v-if="!deployments.length" class="empty-text">{{ $t('deploy.noDeployments') }}</div>
      <el-table v-else :data="deployments" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="task_id" label="Task" width="80" />
        <el-table-column prop="status" :label="$t('tasks.detail.status')" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">
              {{ $t(`deploy.status.${row.status}`) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="preview_url" label="Preview URL" min-width="200">
          <template #default="{ row }">
            <a v-if="row.preview_url && row.status === 'running'" :href="row.preview_url" target="_blank" class="preview-link">
              {{ row.preview_url }}
            </a>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="port" label="Port" width="80" />
        <el-table-column prop="created_at" :label="$t('tasks.detail.createdAt')" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewLogs(row)">{{ $t('deploy.viewLogs') }}</el-button>
            <el-button
              v-if="row.status === 'running'"
              type="warning"
              size="small"
              @click="handleStop(row.id)"
            >{{ $t('deploy.stop') }}</el-button>
            <el-popconfirm :title="$t('deploy.destroyConfirm')" @confirm="handleDestroy(row.id)">
              <template #reference>
                <el-button type="danger" size="small">{{ $t('deploy.destroy') }}</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Build Logs Drawer -->
    <el-drawer v-model="showLogs" :title="$t('deploy.viewLogs')" size="600px">
      <pre class="build-logs">{{ currentLogs }}</pre>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { listDeployments, stopDeployment, destroyDeployment } from '@/api/deploy'
import type { DeploymentItem } from '@/api/deploy'

const { t } = useI18n()
const deployments = ref<DeploymentItem[]>([])
const showLogs = ref(false)
const currentLogs = ref('')

function statusType(status: string) {
  const map: Record<string, string> = { building: 'warning', running: 'success', stopped: 'info', failed: 'danger' }
  return map[status] || 'info'
}

function formatTime(iso?: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

async function fetchDeployments() {
  try { deployments.value = await listDeployments() } catch {}
}

async function viewLogs(row: DeploymentItem) {
  currentLogs.value = row.build_log || 'No logs available'
  showLogs.value = true
}

async function handleStop(id: number) {
  try {
    await stopDeployment(id)
    ElMessage.success(t('deploy.stopSuccess'))
    await fetchDeployments()
  } catch {}
}

async function handleDestroy(id: number) {
  try {
    await destroyDeployment(id)
    ElMessage.success(t('deploy.destroySuccess'))
    await fetchDeployments()
  } catch {}
}

onMounted(fetchDeployments)
</script>

<style scoped>
.deploy-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 22px; color: #303133; margin: 0; }
.empty-text { text-align: center; color: #999; padding: 40px; }
.text-muted { color: #999; }
.preview-link { color: #409eff; text-decoration: none; }
.preview-link:hover { text-decoration: underline; }
.build-logs { background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 12px; white-space: pre-wrap; min-height: 300px; }
</style>
