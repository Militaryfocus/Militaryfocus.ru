<template>
  <div class="card p-6 flex gap-6 animate-pulse">
    <!-- Image skeleton -->
    <div class="flex-shrink-0 hidden md:block">
      <div class="w-48 h-32 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
    </div>
    
    <!-- Content skeleton -->
    <div class="flex-1">
      <!-- Category & Date -->
      <div class="flex items-center gap-3 mb-2">
        <div class="h-3 w-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="h-3 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="h-3 w-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
      
      <!-- Title -->
      <div class="mb-3">
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
        <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
      </div>
      
      <!-- Excerpt -->
      <div class="mb-4">
        <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
        <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
      
      <!-- Footer -->
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center">
            <div class="w-6 h-6 bg-gray-200 dark:bg-gray-700 rounded-full mr-2"></div>
            <div class="h-3 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
          <div class="flex gap-2">
            <div class="h-3 w-12 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div class="h-3 w-14 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        </div>
        <div class="flex gap-4">
          <div class="h-3 w-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div class="h-3 w-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
          <div class="h-3 w-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    </div>
  </div>
</template>