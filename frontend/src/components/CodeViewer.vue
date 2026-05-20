<template>
  <div class="code-viewer">
    <div ref="editorContainer" class="editor-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as monaco from 'monaco-editor'

const props = withDefaults(defineProps<{
  code: string
  language?: string
  readonly?: boolean
  height?: string
}>(), {
  language: 'python',
  readonly: true,
  height: '400px',
})

const editorContainer = ref<HTMLElement>()
let editor: monaco.editor.IStandaloneCodeEditor | null = null

onMounted(() => {
  if (editorContainer.value) {
    editor = monaco.editor.create(editorContainer.value, {
      value: props.code,
      language: props.language,
      readOnly: props.readonly,
      theme: 'vs-dark',
      minimap: { enabled: false },
      fontSize: 13,
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      automaticLayout: true,
      tabSize: 4,
    })
  }
})

watch(() => props.code, (newVal) => {
  if (editor) {
    editor.setValue(newVal)
  }
})

watch(() => props.language, (newVal) => {
  if (editor) {
    const model = editor.getModel()
    if (model) {
      monaco.editor.setModelLanguage(model, newVal)
    }
  }
})

onUnmounted(() => {
  if (editor) {
    editor.dispose()
    editor = null
  }
})
</script>

<style scoped>
.code-viewer {
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #333;
}

.editor-container {
  width: 100%;
  height: v-bind(height);
}
</style>
