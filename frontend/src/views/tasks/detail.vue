<template>
  <div class="task-detail">
    <!-- Header -->
    <div class="detail-header">
      <el-page-header @back="$router.push('/tasks')">
        <template #content>
          <span>{{ $t('tasks.detail.title') }} #{{ taskId }}</span>
        </template>
      </el-page-header>
      <div class="header-actions">
        <el-button
          type="danger"
          :loading="publishing"
          :disabled="task?.status !== 'completed'"
          @click="handlePublish"
        >
          {{ publishing ? $t('deploy.publishing') : $t('deploy.publish') }}
        </el-button>
        <el-button
          type="success"
          :loading="dagRunning"
          :disabled="task?.status === 'running'"
          @click="handleRunDag"
        >
          {{ dagRunning ? $t('dag.running') : $t('dag.runDag') }}
        </el-button>
        <el-button
          :loading="running"
          :disabled="task?.status === 'running'"
          @click="handleRun"
        >
          {{ task?.status === 'running' ? $t('tasks.running') : $t('tasks.run') }}
        </el-button>
      </div>
    </div>

    <!-- Task Info -->
    <el-card v-loading="loading" class="info-card">
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="$t('tasks.detail.prompt')" :span="2">
          {{ task?.prompt }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('tasks.detail.status')">
          <el-tag :type="statusTagType(task?.status)">
            {{ task ? $t(`tasks.status.${task.status}`) : '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('tasks.detail.agent')">
          <el-tag v-if="task?.current_agent" size="small">{{ task.current_agent }}</el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Pipeline Progress -->
    <PipelineProgress
      v-if="dagNodes.length"
      :nodes="dagNodes"
      :current-agent="task?.current_agent || null"
      class="pipeline-card"
    />

    <!-- Tabs -->
    <el-card class="content-card">
      <el-tabs v-model="activeTab">
        <!-- DAG Tab -->
        <el-tab-pane :label="$t('dag.title')" name="dag">
          <DagView :nodes="dagNodes" :edges="dagEdges" @node-click="handleNodeClick" />
          <el-drawer v-model="showNodeDrawer" :title="$t('dag.nodeInfo')" size="400px">
            <div v-if="selectedNode" class="node-detail">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="ID">{{ selectedNode.node_id }}</el-descriptions-item>
                <el-descriptions-item label="Agent">{{ selectedNode.agent }}</el-descriptions-item>
                <el-descriptions-item :label="$t('dag.nodeStatus')">
                  <el-tag :type="statusTagType(selectedNode.status)" size="small">
                    {{ $t(`tasks.status.${selectedNode.status}`) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item :label="$t('dag.duration')">
                  {{ selectedNode.duration_ms ? `${selectedNode.duration_ms}ms` : '-' }}
                </el-descriptions-item>
                <el-descriptions-item :label="$t('dag.tokens')">{{ selectedNode.token_usage || 0 }}</el-descriptions-item>
              </el-descriptions>
              <div v-if="selectedNode.description" class="node-desc">
                <h4>{{ $t('tasks.detail.stepInput') }}</h4>
                <pre>{{ selectedNode.description }}</pre>
              </div>
              <div v-if="selectedNode.error_msg" class="node-error">
                <h4>{{ $t('tasks.detail.stepError') }}</h4>
                <pre>{{ selectedNode.error_msg }}</pre>
              </div>
            </div>
          </el-drawer>
        </el-tab-pane>

        <!-- Artifacts Tab -->
        <el-tab-pane :label="$t('dag.artifacts')" name="artifacts">
          <div v-if="!artifacts.length" class="empty-text">{{ $t('dag.noArtifacts') }}</div>
          <div v-else>
            <el-select v-model="selectedArtifactIdx" class="artifact-select">
              <el-option v-for="(art, idx) in artifacts" :key="idx" :label="art.file_path" :value="idx" />
            </el-select>
            <CodeViewer
              v-if="currentArtifact"
              :code="currentArtifact.content"
              :language="currentArtifact.language || 'python'"
              height="400px"
            />
          </div>
        </el-tab-pane>

        <!-- Review Tab -->
        <el-tab-pane label="Review" name="review">
          <ReviewPanel :review="reviewData" />
        </el-tab-pane>

        <!-- Test Tab -->
        <el-tab-pane label="Tests" name="tests">
          <TestReport :tests="testData" />
        </el-tab-pane>

        <!-- Trace Tab -->
        <el-tab-pane label="Trace" name="trace">
          <TraceTimeline :trace="traceData" />
        </el-tab-pane>

        <!-- Recovery Tab -->
        <el-tab-pane :label="$t('recovery.title')" name="recovery">
          <RecoveryPanel
            :errors="errorLogs"
            :retries="retryHistory"
            :nodes="dagNodes"
            :retrying="retryingAll"
            @retry-all="handleRetryAll"
          />
        </el-tab-pane>

        <!-- Logs Tab -->
        <el-tab-pane :label="$t('tasks.detail.logs')" name="logs">
          <div class="logs-header-bar">
            <el-tag :type="wsConnected ? 'success' : 'danger'" size="small">
              {{ wsConnected ? $t('tasks.detail.connected') : $t('tasks.detail.disconnected') }}
            </el-tag>
          </div>
          <div ref="logsContainer" class="logs-container">
            <div v-if="!logs.length" class="empty-text">{{ $t('tasks.detail.noLogs') }}</div>
            <div v-for="(log, idx) in logs" :key="idx" class="log-line">
              <span class="log-time">{{ log.time }}</span>
              <span :class="['log-event', `log-${log.type}`]">{{ log.message }}</span>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getTask, runTask } from '@/api/tasks'
import { getTaskDag, runTaskDag, getTaskArtifacts } from '@/api/dag'
import { getTaskReview, getTaskTests } from '@/api/review'
import { getTaskErrors, getRetryHistory, retryFailedNodes } from '@/api/recovery'
import { getTaskTrace } from '@/api/metrics'
import { publishTask } from '@/api/deploy'
import type { Task } from '@/api/tasks'
import type { DagNode, DagEdge, Artifact } from '@/api/dag'
import type { ReviewSummary, TestSummary } from '@/api/review'
import type { ErrorLogItem, RetryHistoryItem } from '@/api/recovery'
import type { TaskTrace } from '@/api/metrics'
import DagView from '@/components/DagView.vue'
import CodeViewer from '@/components/CodeViewer.vue'
import ReviewPanel from '@/components/ReviewPanel.vue'
import TestReport from '@/components/TestReport.vue'
import PipelineProgress from '@/components/PipelineProgress.vue'
import RecoveryPanel from '@/components/RecoveryPanel.vue'
import TraceTimeline from '@/components/TraceTimeline.vue'

const route = useRoute()
const { t } = useI18n()
const taskId = Number(route.params.id)

const task = ref<Task | null>(null)
const loading = ref(false)
const running = ref(false)
const dagRunning = ref(false)
const publishing = ref(false)
const activeTab = ref('dag')

// DAG
const dagNodes = ref<DagNode[]>([])
const dagEdges = ref<DagEdge[]>([])
const selectedNode = ref<DagNode | null>(null)
const showNodeDrawer = ref(false)

// Artifacts
const artifacts = ref<Artifact[]>([])
const selectedArtifactIdx = ref(0)
const currentArtifact = computed(() => artifacts.value[selectedArtifactIdx.value] || null)

// Review & Test
const reviewData = ref<ReviewSummary | null>(null)
const testData = ref<TestSummary | null>(null)

// Recovery
const errorLogs = ref<ErrorLogItem[]>([])
const retryHistory = ref<RetryHistoryItem[]>([])
const retryingAll = ref(false)

// Trace
const traceData = ref<TaskTrace | null>(null)

// WebSocket
const wsConnected = ref(false)
const logsContainer = ref<HTMLElement>()
interface LogEntry { time: string; message: string; type: string }
const logs = ref<LogEntry[]>([])
let ws: WebSocket | null = null

function statusTagType(status?: string) {
  const map: Record<string, string> = { pending: 'info', running: '', completed: 'success', failed: 'danger', cancelled: 'warning' }
  return map[status || ''] || 'info'
}

function nowTime() { return new Date().toLocaleTimeString() }

async function fetchTask() {
  loading.value = true
  try { task.value = await getTask(taskId) } catch {} finally { loading.value = false }
}

async function fetchDag() {
  try { const res = await getTaskDag(taskId); dagNodes.value = res.nodes; dagEdges.value = res.edges } catch {}
}

async function fetchArtifacts() {
  try { artifacts.value = await getTaskArtifacts(taskId) } catch {}
}

async function fetchReview() {
  try { reviewData.value = await getTaskReview(taskId) } catch {}
}

async function fetchTests() {
  try { testData.value = await getTaskTests(taskId) } catch {}
}

async function fetchErrors() {
  try { errorLogs.value = await getTaskErrors(taskId) } catch {}
}

async function fetchRetries() {
  try { retryHistory.value = await getRetryHistory(taskId) } catch {}
}

async function fetchTrace() {
  try { traceData.value = await getTaskTrace(taskId) } catch {}
}

async function handleRetryAll() {
  retryingAll.value = true
  try {
    const res = await retryFailedNodes(taskId)
    ElMessage.success(t('recovery.retrySuccess', { n: res.recovered }))
    await Promise.all([fetchDag(), fetchTask(), fetchErrors(), fetchRetries()])
  } catch {} finally { retryingAll.value = false }
}

async function handlePublish() {
  publishing.value = true
  try {
    await publishTask(taskId)
    ElMessage.success(t('deploy.publishSuccess'))
  } catch {} finally { publishing.value = false }
}

async function handleRun() {
  running.value = true
  try { await runTask(taskId); ElMessage.success(t('tasks.runSuccess')); await fetchTask() } catch {} finally { running.value = false }
}

async function handleRunDag() {
  dagRunning.value = true
  try {
    const res = await runTaskDag(taskId)
    dagNodes.value = res.nodes; dagEdges.value = res.edges
    ElMessage.success(t('tasks.runSuccess'))
    await Promise.all([fetchTask(), fetchArtifacts(), fetchReview(), fetchTests()])
  } catch {} finally { dagRunning.value = false }
}

function handleNodeClick(node: DagNode) {
  selectedNode.value = node; showNodeDrawer.value = true
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = `${protocol}//${window.location.host}/api/v1/ws/tasks/${taskId}`
  ws = new WebSocket(url)
  ws.onopen = () => { wsConnected.value = true; logs.value.push({ time: nowTime(), message: t('tasks.detail.connected'), type: 'info' }) }
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      let type = 'info'
      if (data.event?.includes('failed')) type = 'error'
      else if (data.event?.includes('completed')) type = 'success'
      else if (data.event?.includes('started')) type = 'primary'
      logs.value.push({ time: nowTime(), message: `[${data.event}] ${JSON.stringify(data)}`, type })
      if (data.event?.startsWith('node_') || data.event?.startsWith('dag_')) fetchDag()
      if (data.event === 'dag_completed') { fetchTask(); fetchArtifacts(); fetchReview(); fetchTests() }
    } catch { logs.value.push({ time: nowTime(), message: event.data, type: 'info' }) }
    nextTick(() => { if (logsContainer.value) logsContainer.value.scrollTop = logsContainer.value.scrollHeight })
  }
  ws.onclose = () => { wsConnected.value = false; logs.value.push({ time: nowTime(), message: t('tasks.detail.disconnected'), type: 'warning' }) }
  ws.onerror = () => { wsConnected.value = false }
}

onMounted(() => {
  fetchTask(); fetchDag(); fetchArtifacts(); fetchReview(); fetchTests(); fetchErrors(); fetchRetries(); fetchTrace(); connectWebSocket()
})
onUnmounted(() => { if (ws) { ws.close(); ws = null } })
</script>

<style scoped>
.task-detail { padding: 0; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-actions { display: flex; gap: 8px; }
.info-card { margin-bottom: 16px; }
.pipeline-card { margin-bottom: 16px; }
.content-card { margin-bottom: 16px; }
.empty-text { color: #999; text-align: center; padding: 40px; }
.node-detail { padding: 0; }
.node-desc, .node-error { margin-top: 16px; }
.node-desc pre, .node-error pre { background: #f5f7fa; padding: 12px; border-radius: 4px; font-size: 12px; white-space: pre-wrap; word-break: break-all; }
.node-error pre { background: #fef0f0; color: #f56c6c; }
.artifact-select { width: 100%; margin-bottom: 12px; }
.logs-header-bar { margin-bottom: 8px; }
.logs-container { height: 300px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 12px; background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 4px; }
.log-line { margin-bottom: 4px; line-height: 1.6; }
.log-time { color: #6a9955; margin-right: 8px; }
.log-info { color: #d4d4d4; }
.log-primary { color: #569cd6; }
.log-success { color: #6a9955; }
.log-warning { color: #ce9178; }
.log-error { color: #f44747; }
</style>
