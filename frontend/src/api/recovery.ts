import request from '@/utils/request'

export interface ErrorLogItem {
  id: number
  task_id: number
  node_id: string | null
  error_type: string | null
  error_message: string | null
  is_recoverable: boolean
}

export interface RetryHistoryItem {
  id: number
  task_id: number
  node_id: string | null
  attempt: number
  strategy: string | null
  model_used: string | null
  status: string
  duration_ms: number
}

export interface RetryResult {
  message: string
  retried: number
  recovered: number
}

export function getTaskErrors(taskId: number) {
  return request.get<any, ErrorLogItem[]>(`/tasks/${taskId}/errors`)
}

export function getRetryHistory(taskId: number) {
  return request.get<any, RetryHistoryItem[]>(`/tasks/${taskId}/retries`)
}

export function retryFailedNodes(taskId: number, maxRetries: number = 3) {
  return request.post<any, RetryResult>(`/tasks/${taskId}/retry`, { max_retries: maxRetries })
}

export function fixNode(taskId: number, nodeId: string) {
  return request.post<any, { node_id: string; recovered: boolean; status: string }>(`/tasks/${taskId}/nodes/${nodeId}/fix`)
}
