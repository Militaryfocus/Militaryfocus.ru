<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-4">Редактировать пост #{{ id }}</h1>
    <p class="text-gray-600 dark:text-gray-400">Страница редактирования поста</p>
  </div>
</template>

<script setup>
defineProps({
  id: {
    type: String,
    required: true
  }
})

// TODO: Implement edit post view
</script>