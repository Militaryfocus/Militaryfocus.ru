import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter()
  const toast = useToast()
  
  // State
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const refreshToken = ref(localStorage.getItem('refreshToken'))
  const loading = ref(false)
  const showAuthModal = ref(false)
  const redirectPath = ref(null)
  
  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_admin || false)
  const username = computed(() => user.value?.username || '')
  const avatar = computed(() => user.value?.avatar || '/default-avatar.png')
  
  // Actions
  async function login(credentials) {
    loading.value = true
    try {
      const response = await api.post('/auth/login', credentials)
      const { access_token, refresh_token, user: userData } = response.data
      
      // Сохранить токены
      token.value = access_token
      refreshToken.value = refresh_token
      localStorage.setItem('token', access_token)
      localStorage.setItem('refreshToken', refresh_token)
      
      // Сохранить пользователя
      user.value = userData
      
      // Установить токен в API
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      // Закрыть модалку
      showAuthModal.value = false
      
      // Показать уведомление
      toast.success('Вы успешно вошли в систему')
      
      // Перенаправить если нужно
      if (redirectPath.value) {
        router.push(redirectPath.value)
        redirectPath.value = null
      }
      
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка входа'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      loading.value = false
    }
  }
  
  async function register(data) {
    loading.value = true
    try {
      const response = await api.post('/auth/register', data)
      const { message } = response.data
      
      toast.success(message || 'Регистрация успешна! Теперь войдите в систему')
      
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка регистрации'
      const errors = error.response?.data?.errors || {}
      toast.error(message)
      return { success: false, error: message, errors }
    } finally {
      loading.value = false
    }
  }
  
  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // Игнорируем ошибки при выходе
    }
    
    // Очистить данные
    user.value = null
    token.value = null
    refreshToken.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    delete api.defaults.headers.common['Authorization']
    
    // Перенаправить на главную
    router.push('/')
    toast.info('Вы вышли из системы')
  }
  
  async function checkAuth() {
    if (!token.value) return
    
    try {
      const response = await api.get('/auth/me')
      user.value = response.data.user
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    } catch (error) {
      // Токен невалидный
      await logout()
    }
  }
  
  async function refreshAccessToken() {
    if (!refreshToken.value) return false
    
    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken.value
      })
      
      const { access_token } = response.data
      token.value = access_token
      localStorage.setItem('token', access_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      return true
    } catch (error) {
      await logout()
      return false
    }
  }
  
  async function updateProfile(data) {
    loading.value = true
    try {
      const response = await api.put('/users/profile', data)
      user.value = response.data.user
      toast.success('Профиль обновлен')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка обновления профиля'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      loading.value = false
    }
  }
  
  async function changePassword(data) {
    loading.value = true
    try {
      await api.post('/auth/change-password', data)
      toast.success('Пароль успешно изменен')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.error || 'Ошибка изменения пароля'
      toast.error(message)
      return { success: false, error: message }
    } finally {
      loading.value = false
    }
  }
  
  function setRedirectPath(path) {
    redirectPath.value = path
  }
  
  return {
    // State
    user,
    token,
    loading,
    showAuthModal,
    
    // Getters
    isAuthenticated,
    isAdmin,
    username,
    avatar,
    
    // Actions
    login,
    register,
    logout,
    checkAuth,
    refreshAccessToken,
    updateProfile,
    changePassword,
    setRedirectPath
  }
})