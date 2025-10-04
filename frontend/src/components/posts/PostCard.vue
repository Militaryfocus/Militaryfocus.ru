<template>
  <article class="card card-hover group overflow-hidden">
    <RouterLink :to="`/posts/${post.slug}`" class="block">
      <!-- Image -->
      <div class="aspect-w-16 aspect-h-9 bg-gray-200 dark:bg-gray-700 overflow-hidden">
        <img
          v-if="post.image_url"
          :src="post.image_url"
          :alt="post.title"
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        >
        <div v-else class="w-full h-full flex items-center justify-center">
          <DocumentTextIcon class="h-12 w-12 text-gray-400" />
        </div>
      </div>
      
      <!-- Content -->
      <div class="p-6">
        <!-- Category & Date -->
        <div class="flex items-center justify-between mb-3">
          <span 
            v-if="post.category"
            class="inline-flex items-center text-xs font-medium"
            :style="{ color: post.category.color }"
          >
            <div 
              class="w-2 h-2 rounded-full mr-1.5"
              :style="{ backgroundColor: post.category.color }"
            ></div>
            {{ post.category.name }}
          </span>
          <time class="text-xs text-gray-500 dark:text-gray-400">
            {{ formatDate(post.created_at, 'relative') }}
          </time>
        </div>
        
        <!-- Title -->
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
          {{ post.title }}
        </h3>
        
        <!-- Excerpt -->
        <p class="text-gray-600 dark:text-gray-400 text-sm line-clamp-3 mb-4">
          {{ post.excerpt }}
        </p>
        
        <!-- Tags -->
        <div v-if="post.tags && post.tags.length > 0" class="flex flex-wrap gap-2 mb-4">
          <span 
            v-for="tag in post.tags.slice(0, 3)" 
            :key="tag.id"
            class="text-xs text-gray-500 dark:text-gray-400"
          >
            #{{ tag.name }}
          </span>
        </div>
        
        <!-- Footer -->
        <div class="flex items-center justify-between">
          <!-- Author -->
          <div class="flex items-center">
            <img
              :src="post.author.avatar || '/default-avatar.png'"
              :alt="post.author.username"
              class="w-6 h-6 rounded-full mr-2"
            >
            <span class="text-sm text-gray-600 dark:text-gray-400">
              {{ post.author.username }}
            </span>
          </div>
          
          <!-- Stats -->
          <div class="flex items-center space-x-3 text-sm text-gray-500 dark:text-gray-400">
            <span class="flex items-center">
              <EyeIcon class="h-4 w-4 mr-1" />
              {{ formatNumber(post.views) }}
            </span>
            <span class="flex items-center">
              <ChatBubbleLeftIcon class="h-4 w-4 mr-1" />
              {{ post.comments_count }}
            </span>
            <span class="flex items-center">
              <HeartIcon class="h-4 w-4 mr-1" />
              {{ post.likes_count }}
            </span>
          </div>
        </div>
      </div>
    </RouterLink>
    
    <!-- Featured Badge -->
    <div 
      v-if="featured" 
      class="absolute top-4 right-4 bg-yellow-500 text-white text-xs font-medium px-2 py-1 rounded"
    >
      Избранное
    </div>
  </article>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import { 
  DocumentTextIcon, 
  EyeIcon, 
  ChatBubbleLeftIcon, 
  HeartIcon 
} from '@heroicons/vue/24/outline'
import { formatDate, formatNumber } from '@/utils/helpers'

defineProps({
  post: {
    type: Object,
    required: true
  },
  featured: {
    type: Boolean,
    default: false
  }
})
</script>