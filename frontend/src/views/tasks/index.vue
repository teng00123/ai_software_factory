<template>
  <div class="tasks-page">
    <div class="page-header">
      <h2 class="page-title">{{ $t('tasks.title') }}</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        {{ $t('tasks.createTask') }}
      </el-button>
    </div>

    <!-- Filters -->
    <el-card class="filter-card" shadow="never">
      <el-form inline>
        <el-form-item :label="$t('tasks.detail.status')">
          <el-select v-model="filterStatus" clearable :placeholder="$t('common.search')" @change="fetchTasks">
            <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button @click="filterStatus = ''; fetchTasks()">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Task Table -->
    <el-card shadow="never">
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="prompt" :label="$t('tasks.detail.prompt')" show-overflow-tooltip min-width="200" />
        <el-table-column prop="current_agent" :label="$t('tasks.detail.agent')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.current_agent" size="small">{{ row.current_agent }}</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('tasks.detail.status')" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ $t(`tasks.status.${row.status}`) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" :label="$t('tasks.detail.createdAt')" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :loading="row._running"
              :disabled="row.status === 'running'"
              @click="handleRun(row)"
            >
              {{ row.status === 'running' ? $t('tasks.running') : $t('tasks.run') }}
            </el-button>
            <el-button size="small" @click="goDetail(row.id)">
              {{ $t('tasks.viewDetail') }}
            </el-button>
            <el-popconfirm :title="$t('tasks.deleteConfirm')" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" size="small">{{ $t('common.delete') }}</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" :title="$t('tasks.createTask')" width="520px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item :label="$t('tasks.promptLabel')" prop="prompt">
          <el-input
            v-model="createForm.prompt"
            type="textarea"
            :rows="4"
            :placeholder="$t('tasks.promptPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="$t('tasks.agentLabel')">
          <el-select v-model="createForm.current_agent" clearable :placeholder="$t('tasks.agentPlaceholder')">
            <el-option v-for="a in agents" :key="a.name" :label="a.name" :value="a.name">
              <span>{{ a.name }}</span>
              <span class="agent-desc">{{ a.description }}</span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          {{ $t('common.create') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getTasks, createTask, runTask, deleteTask, getAgents } from '@/api/tasks'
import type { Task, AgentInfo } from '@/api/tasks'

const router = useRouter()
const { t } = useI18n()

const tasks = ref<(Task & { _running?: boolean })[]>([])
const agents = ref<AgentInfo[]>([])
const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const filterStatus = ref('')
const createFormRef = ref<FormInstance>()

const createForm = reactive({
  prompt: '',
  current_agent: '',
})

const createRules = computed<FormRules>(() => ({
  prompt: [{ required: true, message: t('tasks.promptRequired'), trigger: 'blur' }],
}))

const statusOptions = computed(() => [
  { value: 'pending', label: t('tasks.status.pending') },
  { value: 'running', label: t('tasks.status.running') },
  { value: 'completed', label: t('tasks.status.completed') },
  { value: 'failed', label: t('tasks.status.failed') },
])

function statusTagType(status: string) {
  const map: Record<string, string> = {
    pending: 'info',
    running: '',
    completed: 'success',
    failed: 'danger',
    cancelled: 'warning',
  }
  return map[status] || 'info'
}

function formatTime(iso: string) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString()
}

async function fetchTasks() {
  loading.value = true
  try {
    const params: any = {}
    if (filterStatus.value) params.status_filter = filterStatus.value
    tasks.value = await getTasks(params)
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function fetchAgents() {
  try {
    agents.value = await getAgents()
  } catch {
    // ignore
  }
}

async function handleCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await createTask({
      prompt: createForm.prompt,
      current_agent: createForm.current_agent || undefined,
    })
    ElMessage.success(t('tasks.createSuccess'))
    showCreateDialog.value = false
    createForm.prompt = ''
    createForm.current_agent = ''
    await fetchTasks()
  } catch {
    // handled by interceptor
  } finally {
    creating.value = false
  }
}

async function handleRun(row: Task & { _running?: boolean }) {
  row._running = true
  try {
    await runTask(row.id)
    ElMessage.success(t('tasks.runSuccess'))
    await fetchTasks()
  } catch {
    // handled by interceptor
  } finally {
    row._running = false
  }
}

async function handleDelete(id: number) {
  try {
    await deleteTask(id)
    ElMessage.success(t('tasks.deleteSuccess'))
    await fetchTasks()
  } catch {
    // handled by interceptor
  }
}

function goDetail(id: number) {
  router.push(`/tasks/${id}`)
}

onMounted(() => {
  fetchTasks()
  fetchAgents()
})
</script>

<style scoped>
.tasks-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-title {
  font-size: 22px;
  color: #303133;
  margin: 0;
}

.filter-card {
  margin-bottom: 16px;
}

.text-muted {
  color: #999;
}

.agent-desc {
  float: right;
  color: #999;
  font-size: 12px;
}
</style>
