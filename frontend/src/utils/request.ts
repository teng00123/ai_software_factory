import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import i18n from '@/i18n'

const { t } = i18n.global

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const { response } = error
    if (response) {
      switch (response.status) {
        case 401:
          localStorage.removeItem('token')
          router.push('/login')
          ElMessage.error(t('request.loginExpired'))
          break
        case 403:
          ElMessage.error(t('request.accessDenied'))
          break
        case 500:
          ElMessage.error(t('request.serverError'))
          break
        default:
          ElMessage.error(response.data?.message || t('request.requestFailed'))
      }
    } else {
      ElMessage.error(t('request.networkError'))
    }
    return Promise.reject(error)
  }
)

export default request
