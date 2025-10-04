<template>
  <div>
    <!-- Hero Section -->
    <section class="bg-gradient-to-r from-primary-600 to-primary-800 text-white">
      <div class="container mx-auto px-4 py-16 md:py-24">
        <div class="max-w-3xl">
          <h1 class="text-4xl md:text-5xl font-bold mb-6">
            Военная аналитика и новости
          </h1>
          <p class="text-xl mb-8 text-primary-100">
            Актуальная информация о военной технике, стратегии и геополитике от экспертов
          </p>
          <div class="flex flex-wrap gap-4">
            <RouterLink to="/posts" class="btn bg-white text-primary-600 hover:bg-gray-100">
              Читать статьи
            </RouterLink>
            <button 
              @click="scrollToCategories"
              class="btn btn-outline border-white text-white hover:bg-white hover:text-primary-600"
            >
              Изучить темы
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats Section -->
    <section class="py-12 bg-gray-50 dark:bg-gray-900">
      <div class="container mx-auto px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="text-center">
            <div class="text-3xl font-bold text-gray-900 dark:text-white">
              {{ stats.posts }}+
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              Статей
            </div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-gray-900 dark:text-white">
              {{ stats.authors }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              Авторов
            </div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-gray-900 dark:text-white">
              {{ stats.categories }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              Категорий
            </div>
          </div>
          <div class="text-center">
            <div class="text-3xl font-bold text-gray-900 dark:text-white">
              {{ stats.views }}K+
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400">
              Просмотров
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Featured Posts -->
    <section class="py-16">
      <div class="container mx-auto px-4">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-3xl font-bold text-gray-900 dark:text-white">
            Избранные статьи
          </h2>
          <RouterLink to="/posts?featured=true" class="link">
            Все избранные →
          </RouterLink>
        </div>
        
        <div v-if="featuredLoading" class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <PostCardSkeleton v-for="i in 3" :key="i" />
        </div>
        
        <div v-else-if="featuredPosts.length > 0" class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <PostCard 
            v-for="post in featuredPosts" 
            :key="post.id" 
            :post="post"
            featured
          />
        </div>
        
        <div v-else class="text-center py-12 text-gray-500">
          Нет избранных статей
        </div>
      </div>
    </section>

    <!-- Categories -->
    <section ref="categoriesSection" class="py-16 bg-gray-50 dark:bg-gray-900">
      <div class="container mx-auto px-4">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Популярные категории
          </h2>
          <p class="text-lg text-gray-600 dark:text-gray-400">
            Изучайте статьи по интересующим вас темам
          </p>
        </div>
        
        <div v-if="categoriesLoading" class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="i in 8" :key="i" class="skeleton h-32 rounded-xl"></div>
        </div>
        
        <div v-else class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <RouterLink
            v-for="category in categories"
            :key="category.id"
            :to="`/category/${category.slug}`"
            class="card card-hover p-6 text-center group"
          >
            <div 
              class="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center text-white text-2xl font-bold"
              :style="{ backgroundColor: category.color }"
            >
              {{ category.name.charAt(0) }}
            </div>
            <h3 class="font-semibold text-gray-900 dark:text-white mb-2">
              {{ category.name }}
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              {{ category.posts_count }} {{ pluralize(category.posts_count, 'статья', 'статьи', 'статей') }}
            </p>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Recent Posts -->
    <section class="py-16">
      <div class="container mx-auto px-4">
        <div class="flex items-center justify-between mb-8">
          <h2 class="text-3xl font-bold text-gray-900 dark:text-white">
            Последние статьи
          </h2>
          <RouterLink to="/posts" class="link">
            Все статьи →
          </RouterLink>
        </div>
        
        <div v-if="recentLoading" class="space-y-6">
          <PostListItemSkeleton v-for="i in 5" :key="i" />
        </div>
        
        <div v-else-if="recentPosts.length > 0" class="space-y-6">
          <PostListItem 
            v-for="post in recentPosts" 
            :key="post.id" 
            :post="post"
          />
        </div>
        
        <div v-else class="text-center py-12 text-gray-500">
          Нет статей
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-16 bg-primary-600 text-white">
      <div class="container mx-auto px-4 text-center">
        <h2 class="text-3xl font-bold mb-4">
          Хотите стать автором?
        </h2>
        <p class="text-xl mb-8 text-primary-100 max-w-2xl mx-auto">
          Присоединяйтесь к нашему сообществу экспертов и делитесь своими знаниями с тысячами читателей
        </p>
        <button 
          @click="authStore.showAuthModal = true"
          class="btn bg-white text-primary-600 hover:bg-gray-100"
        >
          Начать писать
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { postsService } from '@/services/posts'
import { categoriesService } from '@/services/categories'
import { pluralize } from '@/utils/helpers'
import PostCard from '@/components/posts/PostCard.vue'
import PostCardSkeleton from '@/components/posts/PostCardSkeleton.vue'
import PostListItem from '@/components/posts/PostListItem.vue'
import PostListItemSkeleton from '@/components/posts/PostListItemSkeleton.vue'

const authStore = useAuthStore()

// Refs
const categoriesSection = ref(null)

// State
const stats = ref({
  posts: 250,
  authors: 12,
  categories: 8,
  views: 125
})

const featuredPosts = ref([])
const featuredLoading = ref(true)

const recentPosts = ref([])
const recentLoading = ref(true)

const categories = ref([])
const categoriesLoading = ref(true)

// Methods
function scrollToCategories() {
  categoriesSection.value?.scrollIntoView({ behavior: 'smooth' })
}

// Load data
onMounted(async () => {
  // Load featured posts
  try {
    const featuredResponse = await postsService.getPosts({ 
      featured: true, 
      perPage: 3 
    })
    featuredPosts.value = featuredResponse.posts
  } catch (error) {
    console.error('Failed to load featured posts:', error)
  } finally {
    featuredLoading.value = false
  }
  
  // Load recent posts
  try {
    const recentResponse = await postsService.getPosts({ 
      perPage: 5,
      sortBy: 'created_at',
      order: 'desc'
    })
    recentPosts.value = recentResponse.posts
  } catch (error) {
    console.error('Failed to load recent posts:', error)
  } finally {
    recentLoading.value = false
  }
  
  // Load categories
  try {
    const categoriesResponse = await categoriesService.getCategories({
      includeEmpty: false,
      sortBy: 'posts_count',
      limit: 8
    })
    categories.value = categoriesResponse.categories
  } catch (error) {
    console.error('Failed to load categories:', error)
  } finally {
    categoriesLoading.value = false
  }
})
</script>