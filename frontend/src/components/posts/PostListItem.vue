<template>
  <article class="card p-6 flex gap-6">
    <!-- Image -->
    <RouterLink 
      :to="`/posts/${post.slug}`"
      class="flex-shrink-0 hidden md:block"
    >
      <div class="w-48 h-32 bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden">
        <img
          v-if="post.image_url"
          :src="post.image_url"
          :alt="post.title"
          class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
          loading="lazy"
        >
        <div v-else class="w-full h-full flex items-center justify-center">
          <DocumentTextIcon class="h-8 w-8 text-gray-400" />
        </div>
      </div>
    </RouterLink>
    
    <!-- Content -->
    <div class="flex-1">
      <!-- Category & Date -->
      <div class="flex items-center gap-3 mb-2">
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
        <span class="text-xs text-gray-500 dark:text-gray-400">•</span>
        <time class="text-xs text-gray-500 dark:text-gray-400">
          {{ formatDate(post.created_at, 'relative') }}
        </time>
        <span class="text-xs text-gray-500 dark:text-gray-400">•</span>
        <span class="text-xs text-gray-500 dark:text-gray-400">
          {{ post.reading_time }} мин чтения
        </span>
      </div>
      
      <!-- Title -->
      <h3 class="mb-2">
        <RouterLink 
          :to="`/posts/${post.slug}`"
          class="text-xl font-semibold text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
        >
          {{ post.title }}
        </RouterLink>
      </h3>
      
      <!-- Excerpt -->
      <p class="text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
        {{ post.excerpt }}
      </p>
      
      <!-- Footer -->
      <div class="flex items-center justify-between">
        <!-- Author & Tags -->
        <div class="flex items-center gap-4">
          <RouterLink 
            :to="`/author/${post.author.username}`"
            class="flex items-center hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
          >
            <img
              :src="post.author.avatar || '/default-avatar.png'"
              :alt="post.author.username"
              class="w-6 h-6 rounded-full mr-2"
            >
            <span class="text-sm text-gray-600 dark:text-gray-400">
              {{ post.author.username }}
            </span>
          </RouterLink>
          
          <div v-if="post.tags && post.tags.length > 0" class="hidden sm:flex gap-2">
            <RouterLink
              v-for="tag in post.tags.slice(0, 2)"
              :key="tag.id"
              :to="`/tag/${tag.slug}`"
              class="text-xs text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
            >
              #{{ tag.name }}
            </RouterLink>
          </div>
        </div>
        
        <!-- Stats -->
        <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
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
  }
})
</script>