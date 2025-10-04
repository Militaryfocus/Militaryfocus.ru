import axios from 'axios'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

// Создать экземпляр axios
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Добавить токен если есть
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
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // Если 401 и не пытались обновить токен
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const authStore = useAuthStore()
      const refreshed = await authStore.refreshAccessToken()
      
      if (refreshed) {
        // Повторить запрос с новым токеном
        return api(originalRequest)
      } else {
        // Перенаправить на главную
        router.push('/')
      }
    }
    
    return Promise.reject(error)
  }
)

// API методы
export default api

// Вспомогательные функции для API
export const apiHelpers = {
  // Построить query string
  buildQueryString(params) {
    const query = new URLSearchParams()
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        query.append(key, value)
      }
    })
    
    return query.toString()
  },
  
  // Обработать ошибки
  getErrorMessage(error) {
    if (error.response?.data?.error) {
      return error.response.data.error
    }
    
    if (error.response?.data?.message) {
      return error.response.data.message
    }
    
    if (error.message) {
      return error.message
    }
    
    return 'Произошла неизвестная ошибка'
  },
  
  // Получить ошибки валидации
  getValidationErrors(error) {
    if (error.response?.data?.errors) {
      return error.response.data.errors
    }
    
    return {}
  }
}