import api, { apiHelpers } from './api'

export const postsService = {
  // Получить список постов
  async getPosts(params = {}) {
    const query = apiHelpers.buildQueryString({
      page: params.page || 1,
      per_page: params.perPage || 10,
      category_id: params.categoryId,
      tag_id: params.tagId,
      author_id: params.authorId,
      search: params.search,
      sort_by: params.sortBy || 'created_at',
      order: params.order || 'desc'
    })
    
    const response = await api.get(`/posts?${query}`)
    return response.data
  },
  
  // Получить пост по slug
  async getPost(slug) {
    const response = await api.get(`/posts/${slug}`)
    return response.data
  },
  
  // Создать пост
  async createPost(data) {
    const response = await api.post('/posts', data)
    return response.data
  },
  
  // Обновить пост
  async updatePost(id, data) {
    const response = await api.put(`/posts/${id}`, data)
    return response.data
  },
  
  // Удалить пост
  async deletePost(id) {
    const response = await api.delete(`/posts/${id}`)
    return response.data
  },
  
  // Лайкнуть/убрать лайк
  async toggleLike(id) {
    const response = await api.post(`/posts/${id}/like`)
    return response.data
  },
  
  // Добавить/убрать из закладок
  async toggleBookmark(id) {
    const response = await api.post(`/posts/${id}/bookmark`)
    return response.data
  },
  
  // Получить популярные посты
  async getTrendingPosts(days = 7, limit = 10) {
    const response = await api.get(`/posts/trending?days=${days}&limit=${limit}`)
    return response.data
  },
  
  // Получить похожие посты
  async getRelatedPosts(id, limit = 5) {
    const response = await api.get(`/posts/related/${id}?limit=${limit}`)
    return response.data
  }
}