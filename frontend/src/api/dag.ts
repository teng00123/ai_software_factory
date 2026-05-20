import request from '@/utils/request'

export interface DagNode {
  id: number
  node_id: string
  agent: string
  label: string | null
  description: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  depends_on: string[] | null
  output_data: any
  error_msg: string | null
  duration_ms: number | null
  token_usage: number
  cost_usd: string
}

export interface DagEdge {
  source: string
  target: string
}

export interface DagResponse {
  nodes: DagNode[]
  edges: DagEdge[]
}

export interface Artifact {
  id: number
  task_id: number
  node_id: string | null
  file_path: string
  content: string
  language: string | null
}

export function getTaskDag(taskId: number) {
  return request.get<any, DagResponse>(`/tasks/${taskId}/dag`)
}

export function runTaskDag(taskId: number) {
  return request.post<any, DagResponse>(`/tasks/${taskId}/dag/run`)
}

export function getTaskArtifacts(taskId: number) {
  return request.get<any, Artifact[]>(`/tasks/${taskId}/artifacts`)
}
