import request from '@/utils/request'

export interface Task {
  id: number
  prompt: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  current_agent: string | null
  created_at: string
  updated_at: string
  steps: TaskStep[]
}

export interface TaskStep {
  id: number
  agent: string
  input: string | null
  output: string | null
  status: 'pending' | 'running' | 'completed' | 'failed'
  duration: number | null
  token_usage: number
  cost_usd: number
  error_msg: string | null
  created_at: string
  updated_at: string
}

export interface CreateTaskParams {
  prompt: string
  current_agent?: string
}

export function getTasks(params?: { skip?: number; limit?: number; status_filter?: string }) {
  return request.get<any, Task[]>('/tasks/', { params })
}

export function getTask(id: number) {
  return request.get<any, Task>(`/tasks/${id}`)
}

export function createTask(data: CreateTaskParams) {
  return request.post<any, Task>('/tasks/', data)
}

export function runTask(id: number) {
  return request.post<any, Task>(`/tasks/${id}/run`)
}

export function getTaskSteps(id: number) {
  return request.get<any, TaskStep[]>(`/tasks/${id}/steps`)
}

export function deleteTask(id: number) {
  return request.delete<any, void>(`/tasks/${id}`)
}

export interface AgentInfo {
  name: string
  description: string
}

export function getAgents() {
  return request.get<any, AgentInfo[]>('/agents/')
}
