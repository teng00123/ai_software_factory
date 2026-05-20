<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">{{ $t('login.title') }}</h2>
      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        @keyup.enter="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="$t('login.usernamePlaceholder')"
            :prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="$t('login.passwordPlaceholder')"
            :prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ $t('login.loginBtn') }}
          </el-button>
        </el-form-item>
      </el-form>
      <div class="init-admin">
        <el-button type="text" :loading="initLoading" @click="handleInitAdmin">
          {{ $t('login.initAdmin') }}
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { login, initAdmin } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()
const { t } = useI18n()
const formRef = ref<FormInstance>()
const loading = ref(false)
const initLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const rules = computed<FormRules>(() => ({
  username: [{ required: true, message: t('login.usernameRequired'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.passwordRequired'), trigger: 'blur' }],
}))

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await login(loginForm)
    userStore.setToken(res.token)
    userStore.setUsername(res.username)
    ElMessage.success(t('login.loginSuccess'))
    router.push('/dashboard')
  } catch {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

async function handleInitAdmin() {
  initLoading.value = true
  try {
    const res = await initAdmin()
    ElMessage.success(res.message + ' (admin / admin123)')
    loginForm.username = 'admin'
    loginForm.password = 'admin123'
  } catch {
    // Error handled by interceptor
  } finally {
    initLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 20px;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #303133;
  font-size: 24px;
}

.login-btn {
  width: 100%;
}

.init-admin {
  text-align: center;
  margin-top: 12px;
}
</style>
