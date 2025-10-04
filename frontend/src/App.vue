<template>
  <div id="app" class="min-h-screen flex flex-col">
    <!-- Навигация -->
    <AppHeader />
    
    <!-- Основной контент -->
    <main class="flex-1">
      <RouterView v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>
    
    <!-- Футер -->
    <AppFooter />
    
    <!-- Модальные окна и оверлеи -->
    <AuthModal />
    <SearchModal />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import AuthModal from '@/components/modals/AuthModal.vue'
import SearchModal from '@/components/modals/SearchModal.vue'

// Stores
const themeStore = useThemeStore()
const authStore = useAuthStore()

// Инициализация при монтировании
onMounted(() => {
  // Применить сохраненную тему
  themeStore.initTheme()
  
  // Проверить авторизацию
  authStore.checkAuth()
})
</script>

<style>
/* Анимации роутера */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>