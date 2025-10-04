import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // State
  const isDark = ref(false)
  const systemPreference = ref(null)
  
  // Actions
  function initTheme() {
    // Получить системные настройки
    systemPreference.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    
    // Получить сохраненную тему
    const savedTheme = localStorage.getItem('theme')
    
    if (savedTheme) {
      isDark.value = savedTheme === 'dark'
    } else {
      // Использовать системные настройки
      isDark.value = systemPreference.value
    }
    
    applyTheme()
    
    // Слушать изменения системных настроек
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      systemPreference.value = e.matches
      if (!localStorage.getItem('theme')) {
        isDark.value = e.matches
        applyTheme()
      }
    })
  }
  
  function toggleTheme() {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    applyTheme()
  }
  
  function setTheme(dark) {
    isDark.value = dark
    localStorage.setItem('theme', dark ? 'dark' : 'light')
    applyTheme()
  }
  
  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
  
  // Watchers
  watch(isDark, () => {
    applyTheme()
  })
  
  return {
    isDark,
    systemPreference,
    initTheme,
    toggleTheme,
    setTheme
  }
})