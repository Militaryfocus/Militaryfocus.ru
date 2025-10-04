<template>
  <header class="sticky top-0 z-40 bg-white dark:bg-dark-card border-b border-gray-200 dark:border-dark-border">
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center">
          <RouterLink to="/" class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span class="text-white font-bold text-lg">MF</span>
            </div>
            <span class="text-xl font-bold text-gray-900 dark:text-white">Military Focus</span>
          </RouterLink>
        </div>

        <!-- Desktop Navigation -->
        <nav class="hidden md:flex items-center space-x-6">
          <RouterLink 
            to="/posts" 
            class="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
            active-class="text-primary-600 dark:text-primary-400"
          >
            Посты
          </RouterLink>
          
          <div class="relative group">
            <button class="flex items-center text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
              Категории
              <ChevronDownIcon class="ml-1 h-4 w-4" />
            </button>
            
            <!-- Dropdown -->
            <div class="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-dark-card rounded-lg shadow-lg border border-gray-200 dark:border-dark-border opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
              <CategoryDropdown />
            </div>
          </div>
          
          <RouterLink 
            to="/authors" 
            class="text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            Авторы
          </RouterLink>
        </nav>

        <!-- Right side -->
        <div class="flex items-center space-x-4">
          <!-- Search -->
          <button 
            @click="searchStore.showModal = true"
            class="p-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            <MagnifyingGlassIcon class="h-5 w-5" />
          </button>

          <!-- Theme toggle -->
          <button 
            @click="themeStore.toggleTheme()"
            class="p-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            <SunIcon v-if="themeStore.isDark" class="h-5 w-5" />
            <MoonIcon v-else class="h-5 w-5" />
          </button>

          <!-- User menu -->
          <div v-if="authStore.isAuthenticated" class="relative">
            <Menu as="div" class="relative">
              <MenuButton class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                <img 
                  :src="authStore.avatar" 
                  :alt="authStore.username"
                  class="w-8 h-8 rounded-full object-cover"
                >
                <ChevronDownIcon class="h-4 w-4 text-gray-500" />
              </MenuButton>
              
              <transition
                enter-active-class="transition duration-100 ease-out"
                enter-from-class="transform scale-95 opacity-0"
                enter-to-class="transform scale-100 opacity-100"
                leave-active-class="transition duration-75 ease-in"
                leave-from-class="transform scale-100 opacity-100"
                leave-to-class="transform scale-95 opacity-0"
              >
                <MenuItems class="absolute right-0 mt-2 w-48 bg-white dark:bg-dark-card rounded-lg shadow-lg border border-gray-200 dark:border-dark-border focus:outline-none">
                  <MenuItem v-slot="{ active }">
                    <RouterLink
                      to="/profile"
                      :class="[
                        active ? 'bg-gray-100 dark:bg-gray-800' : '',
                        'block px-4 py-2 text-sm text-gray-700 dark:text-gray-300'
                      ]"
                    >
                      Профиль
                    </RouterLink>
                  </MenuItem>
                  
                  <MenuItem v-slot="{ active }">
                    <RouterLink
                      to="/dashboard"
                      :class="[
                        active ? 'bg-gray-100 dark:bg-gray-800' : '',
                        'block px-4 py-2 text-sm text-gray-700 dark:text-gray-300'
                      ]"
                    >
                      Панель управления
                    </RouterLink>
                  </MenuItem>
                  
                  <MenuItem v-slot="{ active }">
                    <RouterLink
                      to="/bookmarks"
                      :class="[
                        active ? 'bg-gray-100 dark:bg-gray-800' : '',
                        'block px-4 py-2 text-sm text-gray-700 dark:text-gray-300'
                      ]"
                    >
                      Закладки
                    </RouterLink>
                  </MenuItem>
                  
                  <hr class="my-1 border-gray-200 dark:border-gray-700">
                  
                  <MenuItem v-slot="{ active }">
                    <button
                      @click="authStore.logout()"
                      :class="[
                        active ? 'bg-gray-100 dark:bg-gray-800' : '',
                        'block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300'
                      ]"
                    >
                      Выйти
                    </button>
                  </MenuItem>
                </MenuItems>
              </transition>
            </Menu>
          </div>
          
          <!-- Login button -->
          <button 
            v-else
            @click="authStore.showAuthModal = true"
            class="btn btn-primary"
          >
            Войти
          </button>

          <!-- Mobile menu button -->
          <button 
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="md:hidden p-2 text-gray-600 dark:text-gray-400"
          >
            <Bars3Icon v-if="!mobileMenuOpen" class="h-6 w-6" />
            <XMarkIcon v-else class="h-6 w-6" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile menu -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform -translate-y-full"
      enter-to-class="transform translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform translate-y-0"
      leave-to-class="transform -translate-y-full"
    >
      <div v-if="mobileMenuOpen" class="md:hidden bg-white dark:bg-dark-card border-t border-gray-200 dark:border-dark-border">
        <nav class="container mx-auto px-4 py-4 space-y-2">
          <RouterLink 
            to="/posts" 
            class="block py-2 text-gray-700 dark:text-gray-300"
            @click="mobileMenuOpen = false"
          >
            Посты
          </RouterLink>
          <RouterLink 
            to="/categories" 
            class="block py-2 text-gray-700 dark:text-gray-300"
            @click="mobileMenuOpen = false"
          >
            Категории
          </RouterLink>
          <RouterLink 
            to="/authors" 
            class="block py-2 text-gray-700 dark:text-gray-300"
            @click="mobileMenuOpen = false"
          >
            Авторы
          </RouterLink>
        </nav>
      </div>
    </transition>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'
import { 
  MagnifyingGlassIcon, 
  SunIcon, 
  MoonIcon, 
  ChevronDownIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/vue/24/outline'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useSearchStore } from '@/stores/search'
import CategoryDropdown from '@/components/common/CategoryDropdown.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const searchStore = useSearchStore()
const mobileMenuOpen = ref(false)
</script>