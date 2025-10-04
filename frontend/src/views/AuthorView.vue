<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-4">Автор: {{ username }}</h1>
    <p class="text-gray-600 dark:text-gray-400">Страница автора</p>
  </div>
</template>

<script setup>
defineProps({
  username: {
    type: String,
    required: true
  }
})

// TODO: Implement author profile view
</script>