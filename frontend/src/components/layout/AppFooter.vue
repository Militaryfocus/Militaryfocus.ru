<template>
  <footer class="bg-gray-900 text-gray-300">
    <div class="container mx-auto px-4 py-12">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <!-- About -->
        <div>
          <h3 class="text-white font-semibold mb-4">О проекте</h3>
          <p class="text-sm text-gray-400">
            Military Focus - военный блог с актуальной аналитикой, новостями и экспертными мнениями о военной технике и стратегии.
          </p>
        </div>

        <!-- Quick Links -->
        <div>
          <h3 class="text-white font-semibold mb-4">Быстрые ссылки</h3>
          <ul class="space-y-2 text-sm">
            <li>
              <RouterLink to="/posts" class="hover:text-white transition-colors">
                Все посты
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/categories" class="hover:text-white transition-colors">
                Категории
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/authors" class="hover:text-white transition-colors">
                Авторы
              </RouterLink>
            </li>
            <li>
              <RouterLink to="/about" class="hover:text-white transition-colors">
                О нас
              </RouterLink>
            </li>
          </ul>
        </div>

        <!-- Categories -->
        <div>
          <h3 class="text-white font-semibold mb-4">Популярные категории</h3>
          <ul class="space-y-2 text-sm">
            <li v-for="category in popularCategories" :key="category.id">
              <RouterLink 
                :to="`/category/${category.slug}`" 
                class="hover:text-white transition-colors"
              >
                {{ category.name }}
              </RouterLink>
            </li>
          </ul>
        </div>

        <!-- Newsletter -->
        <div>
          <h3 class="text-white font-semibold mb-4">Подписка на новости</h3>
          <p class="text-sm text-gray-400 mb-4">
            Получайте последние новости и аналитику прямо на почту
          </p>
          <form @submit.prevent="subscribeNewsletter" class="space-y-2">
            <input
              v-model="email"
              type="email"
              placeholder="Ваш email"
              class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
              required
            >
            <button 
              type="submit"
              class="w-full btn btn-primary"
              :disabled="subscribing"
            >
              {{ subscribing ? 'Подписка...' : 'Подписаться' }}
            </button>
          </form>
        </div>
      </div>

      <!-- Bottom -->
      <div class="mt-12 pt-8 border-t border-gray-800">
        <div class="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div class="text-sm text-gray-400">
            © {{ currentYear }} Military Focus. Все права защищены.
          </div>
          
          <div class="flex space-x-6">
            <a href="/privacy" class="text-sm text-gray-400 hover:text-white transition-colors">
              Конфиденциальность
            </a>
            <a href="/terms" class="text-sm text-gray-400 hover:text-white transition-colors">
              Условия использования
            </a>
            <a href="/contact" class="text-sm text-gray-400 hover:text-white transition-colors">
              Контакты
            </a>
          </div>
          
          <!-- Social links -->
          <div class="flex space-x-4">
            <a 
              href="https://twitter.com/militaryfocus" 
              target="_blank"
              rel="noopener noreferrer"
              class="text-gray-400 hover:text-white transition-colors"
            >
              <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
              </svg>
            </a>
            
            <a 
              href="https://telegram.me/militaryfocus" 
              target="_blank"
              rel="noopener noreferrer"
              class="text-gray-400 hover:text-white transition-colors"
            >
              <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.56c-.21 2.27-1.13 7.75-1.6 10.28-.2 1.07-.59 1.43-.96 1.47-.82.08-1.44-.54-2.24-1.06-1.24-.82-1.95-1.33-3.15-2.13-1.39-.93-.49-1.44.3-2.27.21-.22 3.82-3.5 3.89-3.8.01-.04.01-.19-.07-.27-.08-.08-.2-.05-.28-.04-.12.03-2.07 1.32-5.85 3.87-.55.38-1.05.57-1.5.56-.49-.01-1.44-.28-2.15-.51-.87-.28-1.56-.43-1.5-.91.03-.25.38-.51 1.04-.78 4.07-1.77 6.78-2.95 8.14-3.52 3.87-1.63 4.68-1.91 5.2-1.92.12 0 .37.03.54.17.14.12.18.28.2.46-.01.06.01.24 0 .38z"/>
              </svg>
            </a>
            
            <a 
              href="/rss" 
              class="text-gray-400 hover:text-white transition-colors"
            >
              <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 5c7.18 0 13 5.82 13 13M6 11a7 7 0 017 7m-6 0a1 1 0 11-2 0 1 1 0 012 0z" />
              </svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useToast } from 'vue-toastification'
import { categoriesService } from '@/services/categories'

const toast = useToast()
const email = ref('')
const subscribing = ref(false)
const popularCategories = ref([])

const currentYear = computed(() => new Date().getFullYear())

async function subscribeNewsletter() {
  subscribing.value = true
  
  // TODO: Реализовать подписку на рассылку
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  toast.success('Вы успешно подписались на рассылку!')
  email.value = ''
  subscribing.value = false
}

onMounted(async () => {
  try {
    const response = await categoriesService.getCategories({ limit: 5 })
    popularCategories.value = response.categories
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
})
</script>