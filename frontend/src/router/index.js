import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

// Импорт views
import HomeView from '@/views/HomeView.vue'
import PostsView from '@/views/PostsView.vue'
import PostView from '@/views/PostView.vue'
import CategoryView from '@/views/CategoryView.vue'
import TagView from '@/views/TagView.vue'
import AuthorView from '@/views/AuthorView.vue'
import ProfileView from '@/views/ProfileView.vue'
import DashboardView from '@/views/DashboardView.vue'
import CreatePostView from '@/views/CreatePostView.vue'
import EditPostView from '@/views/EditPostView.vue'
import SettingsView from '@/views/SettingsView.vue'
import BookmarksView from '@/views/BookmarksView.vue'
import NotFoundView from '@/views/NotFoundView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    } else {
      return { top: 0 }
    }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'Главная' }
    },
    {
      path: '/posts',
      name: 'posts',
      component: PostsView,
      meta: { title: 'Все посты' }
    },
    {
      path: '/posts/:slug',
      name: 'post',
      component: PostView,
      props: true
    },
    {
      path: '/category/:slug',
      name: 'category',
      component: CategoryView,
      props: true
    },
    {
      path: '/tag/:slug',
      name: 'tag',
      component: TagView,
      props: true
    },
    {
      path: '/author/:username',
      name: 'author',
      component: AuthorView,
      props: true
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { requiresAuth: true, title: 'Профиль' }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true, title: 'Панель управления' }
    },
    {
      path: '/create',
      name: 'create-post',
      component: CreatePostView,
      meta: { requiresAuth: true, title: 'Создать пост' }
    },
    {
      path: '/edit/:id',
      name: 'edit-post',
      component: EditPostView,
      props: true,
      meta: { requiresAuth: true, title: 'Редактировать пост' }
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true, title: 'Настройки' }
    },
    {
      path: '/bookmarks',
      name: 'bookmarks',
      component: BookmarksView,
      meta: { requiresAuth: true, title: 'Закладки' }
    },
    {
      path: '/404',
      name: 'not-found',
      component: NotFoundView,
      meta: { title: 'Страница не найдена' }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/404'
    }
  ]
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  // Начать индикатор загрузки
  NProgress.start()
  
  // Проверка авторизации
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Сохранить путь для редиректа после логина
    authStore.setRedirectPath(to.fullPath)
    
    // Показать модалку логина
    authStore.showAuthModal = true
    
    next(false)
  } else {
    next()
  }
})

router.afterEach((to) => {
  // Завершить индикатор загрузки
  NProgress.done()
  
  // Установить заголовок страницы
  const defaultTitle = 'Military Focus'
  document.title = to.meta.title ? `${to.meta.title} | ${defaultTitle}` : defaultTitle
})

export default router