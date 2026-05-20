import request from '@/utils/request'

export interface DeploymentItem {
  id: number
  task_id: number
  status: 'building' | 'running' | 'stopped' | 'failed'
  container_id: string | null
  preview_url: string | null
  port: number | null
  build_log: string | null
  dockerfile: string | null
  compose_yaml: string | null
  created_at: string | null
  stopped_at: string | null
}

export interface GitCommit {
  commit_hash: string
  message: string
  files_changed: number
  branch: string
  timestamp: string
}

export interface PublishResult {
  git: GitCommit
  deployment: DeploymentItem
}

export function deployPreview(taskId: number) {
  return request.post<any, DeploymentItem>('/deploy/preview', null, { params: { task_id: taskId } })
}

export function getDeployment(id: number) {
  return request.get<any, DeploymentItem>(`/deploy/preview/${id}`)
}

export function listDeployments(taskId?: number) {
  return request.get<any, DeploymentItem[]>('/deploy/preview', { params: taskId ? { task_id: taskId } : {} })
}

export function stopDeployment(id: number) {
  return request.post<any, DeploymentItem>(`/deploy/preview/${id}/stop`)
}

export function destroyDeployment(id: number) {
  return request.delete<any, void>(`/deploy/preview/${id}`)
}

export function getDeployLogs(id: number) {
  return request.get<any, { logs: string }>(`/deploy/preview/${id}/logs`)
}

export function publishTask(taskId: number) {
  return request.post<any, PublishResult>('/deploy/publish', null, { params: { task_id: taskId } })
}
