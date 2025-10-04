<template>
  <div class="min-h-[60vh] flex items-center justify-center">
    <div class="text-center">
      <h1 class="text-9xl font-bold text-gray-200 dark:text-gray-800">404</h1>
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
        Страница не найдена
      </h2>
      <p class="text-gray-600 dark:text-gray-400 mb-8">
        К сожалению, запрашиваемая страница не существует
      </p>
      <RouterLink to="/" class="btn btn-primary">
        Вернуться на главную
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>