<template>
  <div class="py-2">
    <div v-if="loading" class="px-4 py-2 text-sm text-gray-500">
      Загрузка...
    </div>
    
    <div v-else-if="categories.length === 0" class="px-4 py-2 text-sm text-gray-500">
      Нет категорий
    </div>
    
    <div v-else>
      <RouterLink
        v-for="category in categories"
        :key="category.id"
        :to="`/category/${category.slug}`"
        class="flex items-center justify-between px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        <div class="flex items-center">
          <div 
            class="w-3 h-3 rounded-full mr-2"
            :style="{ backgroundColor: category.color }"
          ></div>
          <span>{{ category.name }}</span>
        </div>
        <span class="text-xs text-gray-500">
          {{ category.posts_count }}
        </span>
      </RouterLink>
      
      <hr class="my-2 border-gray-200 dark:border-gray-700">
      
      <RouterLink
        to="/categories"
        class="block px-4 py-2 text-sm text-primary-600 dark:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      >
        Все категории →
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { categoriesService } from '@/services/categories'

const loading = ref(true)
const categories = ref([])

onMounted(async () => {
  try {
    const response = await categoriesService.getCategories({ 
      includeEmpty: false,
      sortBy: 'posts_count',
      limit: 8
    })
    categories.value = response.categories
  } catch (error) {
    console.error('Failed to load categories:', error)
  } finally {
    loading.value = false
  }
})
</script>