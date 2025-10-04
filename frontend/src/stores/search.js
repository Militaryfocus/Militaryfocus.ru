import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useSearchStore = defineStore('search', () => {
  // State
  const showModal = ref(false)
  const recentSearches = ref([])
  const popularSearches = ref([])
  
  // Actions
  async function search(query) {
    if (!query) return { posts: [], categories: [], tags: [], users: [] }
    
    try {
      // Parallel search requests
      const [postsRes, categoriesRes, tagsRes, usersRes] = await Promise.all([
        api.get(`/posts?search=${encodeURIComponent(query)}&per_page=5`),
        api.get(`/categories?search=${encodeURIComponent(query)}&limit=5`),
        api.get(`/tags?search=${encodeURIComponent(query)}&limit=10`),
        api.get(`/users/search?q=${encodeURIComponent(query)}&limit=5`)
      ])
      
      // Save to recent searches
      addToRecentSearches(query)
      
      return {
        posts: postsRes.data.posts || [],
        categories: categoriesRes.data.categories || [],
        tags: tagsRes.data.tags || [],
        users: usersRes.data.users || []
      }
    } catch (error) {
      console.error('Search error:', error)
      return { posts: [], categories: [], tags: [], users: [] }
    }
  }
  
  function addToRecentSearches(query) {
    // Remove if already exists
    recentSearches.value = recentSearches.value.filter(q => q !== query)
    
    // Add to beginning
    recentSearches.value.unshift(query)
    
    // Keep only last 10
    if (recentSearches.value.length > 10) {
      recentSearches.value = recentSearches.value.slice(0, 10)
    }
    
    // Save to localStorage
    localStorage.setItem('recentSearches', JSON.stringify(recentSearches.value))
  }
  
  function loadRecentSearches() {
    const saved = localStorage.getItem('recentSearches')
    if (saved) {
      try {
        recentSearches.value = JSON.parse(saved)
      } catch (e) {
        recentSearches.value = []
      }
    }
  }
  
  function clearRecentSearches() {
    recentSearches.value = []
    localStorage.removeItem('recentSearches')
  }
  
  // Load recent searches on init
  loadRecentSearches()
  
  return {
    showModal,
    recentSearches,
    popularSearches,
    search,
    addToRecentSearches,
    clearRecentSearches
  }
})