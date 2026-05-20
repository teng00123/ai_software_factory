import request from '@/utils/request'

export interface ReviewComment {
  id: number
  task_id: number
  node_id: string | null
  file_path: string | null
  line_number: number | null
  severity: 'info' | 'warning' | 'error'
  category: string | null
  message: string
  suggestion: string | null
}

export interface ReviewSummary {
  total: number
  errors: number
  warnings: number
  infos: number
  comments: ReviewComment[]
}

export interface TestResultItem {
  id: number
  task_id: number
  node_id: string | null
  test_name: string
  status: 'passed' | 'failed' | 'error' | 'skipped'
  duration_ms: number
  error_msg: string | null
}

export interface TestSummary {
  total: number
  passed: number
  failed: number
  errors: number
  skipped: number
  results: TestResultItem[]
}

export function getTaskReview(taskId: number) {
  return request.get<any, ReviewSummary>(`/tasks/${taskId}/review`)
}

export function getTaskTests(taskId: number) {
  return request.get<any, TestSummary>(`/tasks/${taskId}/tests`)
}
