import api, { apiHelpers } from './api'

export const categoriesService = {
  // Получить список категорий
  async getCategories(params = {}) {
    const query = apiHelpers.buildQueryString({
      include_empty: params.includeEmpty !== false,
      sort_by: params.sortBy || 'name',
      limit: params.limit
    })
    
    const response = await api.get(`/categories?${query}`)
    return response.data
  },
  
  // Получить категорию по slug
  async getCategory(slug) {
    const response = await api.get(`/categories/${slug}`)
    return response.data
  },
  
  // Получить посты категории
  async getCategoryPosts(slug, params = {}) {
    const query = apiHelpers.buildQueryString({
      page: params.page || 1,
      per_page: params.perPage || 10
    })
    
    const response = await api.get(`/categories/${slug}/posts?${query}`)
    return response.data
  },
  
  // Получить дерево категорий
  async getCategoryTree() {
    const response = await api.get('/categories/tree')
    return response.data
  },
  
  // Создать категорию (admin)
  async createCategory(data) {
    const response = await api.post('/categories', data)
    return response.data
  },
  
  // Обновить категорию (admin)
  async updateCategory(id, data) {
    const response = await api.put(`/categories/${id}`, data)
    return response.data
  },
  
  // Удалить категорию (admin)
  async deleteCategory(id) {
    const response = await api.delete(`/categories/${id}`)
    return response.data
  }
}