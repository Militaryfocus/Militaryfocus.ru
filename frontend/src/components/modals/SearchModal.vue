<template>
  <TransitionRoot appear :show="searchStore.showModal" as="template">
    <Dialog as="div" @close="closeModal" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black bg-opacity-50" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-start justify-center p-4 pt-20">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white dark:bg-dark-card shadow-xl transition-all">
              <!-- Search Input -->
              <div class="relative">
                <MagnifyingGlassIcon class="absolute left-4 top-4 h-6 w-6 text-gray-400" />
                <input
                  ref="searchInput"
                  v-model="searchQuery"
                  type="text"
                  class="w-full pl-12 pr-4 py-4 text-lg bg-transparent border-b border-gray-200 dark:border-gray-700 focus:outline-none focus:border-primary-500"
                  placeholder="Поиск постов, категорий, тегов..."
                  @input="performSearch"
                >
                <button
                  v-if="searchQuery"
                  @click="clearSearch"
                  class="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon class="h-5 w-5" />
                </button>
              </div>

              <!-- Search Results -->
              <div class="max-h-96 overflow-y-auto">
                <!-- Loading -->
                <div v-if="loading" class="p-8 text-center">
                  <div class="inline-flex items-center">
                    <svg class="animate-spin h-5 w-5 mr-3 text-gray-400" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Поиск...
                  </div>
                </div>

                <!-- No Results -->
                <div v-else-if="searchQuery && !hasResults" class="p-8 text-center text-gray-500">
                  <MagnifyingGlassIcon class="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>По запросу "{{ searchQuery }}" ничего не найдено</p>
                </div>

                <!-- Results -->
                <div v-else-if="hasResults" class="py-4">
                  <!-- Posts -->
                  <div v-if="results.posts.length > 0" class="mb-6">
                    <h3 class="px-4 text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                      Посты
                    </h3>
                    <div class="space-y-1">
                      <RouterLink
                        v-for="post in results.posts"
                        :key="post.id"
                        :to="`/posts/${post.slug}`"
                        @click="closeModal"
                        class="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div class="flex items-start">
                          <DocumentTextIcon class="h-5 w-5 text-gray-400 mt-0.5 mr-3" />
                          <div class="flex-1">
                            <h4 class="text-sm font-medium text-gray-900 dark:text-white">
                              {{ post.title }}
                            </h4>
                            <p class="text-sm text-gray-500 mt-1 line-clamp-2">
                              {{ post.excerpt }}
                            </p>
                          </div>
                        </div>
                      </RouterLink>
                    </div>
                  </div>

                  <!-- Categories -->
                  <div v-if="results.categories.length > 0" class="mb-6">
                    <h3 class="px-4 text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                      Категории
                    </h3>
                    <div class="space-y-1">
                      <RouterLink
                        v-for="category in results.categories"
                        :key="category.id"
                        :to="`/category/${category.slug}`"
                        @click="closeModal"
                        class="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div class="flex items-center">
                          <FolderIcon class="h-5 w-5 text-gray-400 mr-3" />
                          <span class="text-sm text-gray-900 dark:text-white">
                            {{ category.name }}
                          </span>
                        </div>
                      </RouterLink>
                    </div>
                  </div>

                  <!-- Tags -->
                  <div v-if="results.tags.length > 0" class="mb-6">
                    <h3 class="px-4 text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                      Теги
                    </h3>
                    <div class="px-4 flex flex-wrap gap-2">
                      <RouterLink
                        v-for="tag in results.tags"
                        :key="tag.id"
                        :to="`/tag/${tag.slug}`"
                        @click="closeModal"
                        class="badge badge-primary"
                      >
                        #{{ tag.name }}
                      </RouterLink>
                    </div>
                  </div>

                  <!-- Users -->
                  <div v-if="results.users.length > 0" class="mb-6">
                    <h3 class="px-4 text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                      Авторы
                    </h3>
                    <div class="space-y-1">
                      <RouterLink
                        v-for="user in results.users"
                        :key="user.id"
                        :to="`/author/${user.username}`"
                        @click="closeModal"
                        class="block px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <div class="flex items-center">
                          <img
                            :src="user.avatar || '/default-avatar.png'"
                            :alt="user.username"
                            class="h-8 w-8 rounded-full mr-3"
                          >
                          <div>
                            <div class="text-sm font-medium text-gray-900 dark:text-white">
                              {{ user.username }}
                            </div>
                            <div class="text-xs text-gray-500">
                              {{ user.posts_count }} постов
                            </div>
                          </div>
                        </div>
                      </RouterLink>
                    </div>
                  </div>
                </div>

                <!-- Quick Links -->
                <div v-else class="p-4">
                  <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">
                    Быстрые ссылки
                  </h3>
                  <div class="grid grid-cols-2 gap-2">
                    <RouterLink
                      to="/posts"
                      @click="closeModal"
                      class="flex items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <DocumentTextIcon class="h-5 w-5 text-gray-400 mr-2" />
                      <span class="text-sm">Все посты</span>
                    </RouterLink>
                    
                    <RouterLink
                      to="/categories"
                      @click="closeModal"
                      class="flex items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <FolderIcon class="h-5 w-5 text-gray-400 mr-2" />
                      <span class="text-sm">Категории</span>
                    </RouterLink>
                    
                    <RouterLink
                      to="/tags"
                      @click="closeModal"
                      class="flex items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <TagIcon class="h-5 w-5 text-gray-400 mr-2" />
                      <span class="text-sm">Теги</span>
                    </RouterLink>
                    
                    <RouterLink
                      to="/authors"
                      @click="closeModal"
                      class="flex items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    >
                      <UserIcon class="h-5 w-5 text-gray-400 mr-2" />
                      <span class="text-sm">Авторы</span>
                    </RouterLink>
                  </div>
                </div>
              </div>

              <!-- Footer -->
              <div class="px-4 py-3 bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 flex items-center justify-between">
                <div>
                  Нажмите <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">ESC</kbd> для закрытия
                </div>
                <div>
                  Используйте <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">↑</kbd> 
                  <kbd class="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">↓</kbd> для навигации
                </div>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Dialog, DialogPanel, TransitionChild, TransitionRoot } from '@headlessui/vue'
import { 
  MagnifyingGlassIcon, 
  XMarkIcon,
  DocumentTextIcon,
  FolderIcon,
  TagIcon,
  UserIcon
} from '@heroicons/vue/24/outline'
import { useSearchStore } from '@/stores/search'
import { debounce } from '@/utils/helpers'

const searchStore = useSearchStore()
const searchInput = ref(null)
const searchQuery = ref('')
const loading = ref(false)
const results = ref({
  posts: [],
  categories: [],
  tags: [],
  users: []
})

const hasResults = computed(() => {
  return results.value.posts.length > 0 ||
         results.value.categories.length > 0 ||
         results.value.tags.length > 0 ||
         results.value.users.length > 0
})

// Focus input when modal opens
watch(() => searchStore.showModal, (newVal) => {
  if (newVal) {
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

const performSearch = debounce(async () => {
  if (!searchQuery.value || searchQuery.value.length < 2) {
    results.value = { posts: [], categories: [], tags: [], users: [] }
    return
  }
  
  loading.value = true
  
  try {
    const searchResults = await searchStore.search(searchQuery.value)
    results.value = searchResults
  } catch (error) {
    console.error('Search error:', error)
  } finally {
    loading.value = false
  }
}, 300)

function clearSearch() {
  searchQuery.value = ''
  results.value = { posts: [], categories: [], tags: [], users: [] }
}

function closeModal() {
  searchStore.showModal = false
  clearSearch()
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Open search with Cmd/Ctrl + K
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    searchStore.showModal = true
  }
})
</script>