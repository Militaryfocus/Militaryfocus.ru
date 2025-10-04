<template>
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-4">Тег: {{ slug }}</h1>
    <p class="text-gray-600 dark:text-gray-400">Страница тега</p>
  </div>
</template>

<script setup>
defineProps({
  slug: {
    type: String,
    required: true
  }
})

// TODO: Implement tag view
</script>