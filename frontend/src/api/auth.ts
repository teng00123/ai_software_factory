import request from '@/utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  token: string
  username: string
}

export function login(data: LoginParams) {
  return request.post<any, LoginResult>('/auth/login', data)
}

export function getUserInfo() {
  return request.get<any, { username: string; role: string }>('/auth/me')
}

export function initAdmin() {
  return request.post<any, { message: string; username: string }>('/auth/init')
}
