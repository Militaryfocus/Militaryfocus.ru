import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import './style.css'

// Создание приложения
const app = createApp(App)

// Pinia store
app.use(createPinia())

// Router
app.use(router)

// Toast notifications
app.use(Toast, {
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnFocusLoss: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false
})

// Глобальные свойства
app.config.globalProperties.$filters = {
  formatDate(date) {
    if (!date) return ''
    return new Date(date).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  },
  formatDateTime(date) {
    if (!date) return ''
    return new Date(date).toLocaleString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  },
  truncate(text, length = 100) {
    if (!text || text.length <= length) return text
    return text.substring(0, length) + '...'
  }
}

// Монтирование приложения
app.mount('#app')