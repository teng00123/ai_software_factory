import request from '@/utils/request'

export interface MetricsOverview {
  total_tasks: number
  status_counts: Record<string, number>
  total_tokens: number
  total_cost_usd: number
  total_dag_nodes: number
}

export interface AgentStat {
  agent: string
  executions: number
  total_tokens: number
  total_cost_usd: number
  avg_latency_ms: number
}

export interface CostTrendItem {
  date: string
  cost_usd: number
  tokens: number
}

export interface TraceItem {
  node_id: string
  agent: string
  label: string
  status: string
  duration_ms: number
  token_usage: number
  cost_usd: number
  start_offset_ms: number
}

export interface TaskTrace {
  task_id: number
  total_duration_ms: number
  total_tokens: number
  total_cost_usd: number
  trace: TraceItem[]
}

export interface ReplayStep {
  step_index: number
  event: string
  node_id: string | null
  state: any
  timestamp: string | null
}

export interface TaskReplay {
  task_id: number
  total_steps: number
  steps: ReplayStep[]
}

export function getMetricsOverview() {
  return request.get<any, MetricsOverview>('/metrics/overview')
}

export function getAgentStats() {
  return request.get<any, AgentStat[]>('/metrics/agents')
}

export function getCostTrend(days: number = 7) {
  return request.get<any, CostTrendItem[]>('/metrics/cost', { params: { days } })
}

export function getTaskTrace(taskId: number) {
  return request.get<any, TaskTrace>(`/metrics/tasks/${taskId}/trace`)
}

export function getTaskReplay(taskId: number) {
  return request.get<any, TaskReplay>(`/metrics/tasks/${taskId}/replay`)
}
