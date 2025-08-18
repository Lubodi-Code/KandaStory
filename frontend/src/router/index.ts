import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import VerifyEmailView from '../views/VerifyEmailView.vue'
import CharactersView from '../views/CharactersView.vue'
import RoomsView from '../views/RoomsView.vue'
import RoomDetailView from '../views/RoomDetailView.vue'
import WorldsView from '../views/WorldsView.vue'
import GameView from '../views/GameView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: VerifyEmailView
    },
    {
      path: '/characters',
      name: 'characters',
      component: CharactersView,
      meta: { requiresAuth: true }
    },
    {
      path: '/worlds',
      name: 'worlds',
      component: WorldsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/rooms',
      name: 'rooms',
      component: RoomsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/my-games',
      name: 'my-games',
      component: () => import('../views/MyGamesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/rooms/:id',
      name: 'room-detail',
      component: RoomDetailView,
      meta: { requiresAuth: true }
    },
    {
      path: '/game/:id',
      name: 'game',
      component: GameView,
      meta: { requiresAuth: true }
    }
  ]
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
