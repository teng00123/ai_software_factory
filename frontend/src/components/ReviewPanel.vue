<template>
  <div class="review-panel">
    <div v-if="!review" class="empty-text">{{ $t('dag.noArtifacts') }}</div>
    <template v-else>
      <!-- Summary -->
      <div class="review-summary">
        <el-tag type="danger" size="small">{{ review.errors }} errors</el-tag>
        <el-tag type="warning" size="small">{{ review.warnings }} warnings</el-tag>
        <el-tag type="info" size="small">{{ review.infos }} info</el-tag>
      </div>
      <!-- Comments -->
      <div class="comment-list">
        <div v-for="comment in review.comments" :key="comment.id" :class="['comment-item', `comment-${comment.severity}`]">
          <div class="comment-header">
            <el-tag :type="severityType(comment.severity)" size="small">{{ comment.severity }}</el-tag>
            <span class="comment-file" v-if="comment.file_path">
              {{ comment.file_path }}<span v-if="comment.line_number">:{{ comment.line_number }}</span>
            </span>
            <el-tag v-if="comment.category" size="small" type="info">{{ comment.category }}</el-tag>
          </div>
          <div class="comment-message">{{ comment.message }}</div>
          <div v-if="comment.suggestion" class="comment-suggestion">
            <strong>Suggestion:</strong>
            <code>{{ comment.suggestion }}</code>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import type { ReviewSummary } from '@/api/review'

defineProps<{ review: ReviewSummary | null }>()

function severityType(severity: string) {
  const map: Record<string, string> = { error: 'danger', warning: 'warning', info: 'info' }
  return map[severity] || 'info'
}
</script>

<style scoped>
.review-panel { padding: 0; }
.empty-text { text-align: center; color: #999; padding: 40px; }
.review-summary { display: flex; gap: 8px; margin-bottom: 16px; }
.comment-list { display: flex; flex-direction: column; gap: 12px; }
.comment-item { padding: 12px; border-radius: 4px; border-left: 3px solid #ddd; background: #fafafa; }
.comment-error { border-left-color: #f56c6c; background: #fef0f0; }
.comment-warning { border-left-color: #e6a23c; background: #fdf6ec; }
.comment-info { border-left-color: #909399; }
.comment-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.comment-file { font-family: monospace; font-size: 12px; color: #606266; }
.comment-message { font-size: 14px; color: #303133; }
.comment-suggestion { margin-top: 8px; font-size: 12px; color: #606266; }
.comment-suggestion code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
</style>
