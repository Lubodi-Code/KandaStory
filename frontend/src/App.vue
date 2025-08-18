<template>
  <div id="app" class="min-h-screen">
    <nav class="sticky top-0 z-50 bg-navy-900/95 text-white shadow backdrop-blur">
      <div class="container mx-auto flex flex-wrap items-center justify-between px-4 py-3 gap-2">
        <router-link to="/" class="flex items-center gap-3 group flex-shrink-0">
          <img :src="logoUrl" alt="KandaStory" class="h-12 w-12 md:h-14 md:w-14 rounded-md shadow-sm" />
          <span class="text-2xl md:text-3xl font-semibold tracking-wide">
            <span class="text-gold-400">Kanda</span><span class="text-emerald-300">Story</span>
          </span>
        </router-link>

  <div v-if="authStore.isAuthenticated" class="flex-1 flex items-center gap-3 justify-end flex-wrap">
          <router-link to="/characters" class="nav-link">Personajes</router-link>
          <router-link to="/worlds" class="nav-link">Mundos</router-link>
          <router-link to="/rooms" class="nav-link">Salas</router-link>
          <router-link to="/my-games" class="nav-link">Mis partidas</router-link>
      <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-700/30 border border-emerald-500/40">
            <span class="text-emerald-300 text-xs">👤</span>
            <span class="text-emerald-100 text-sm font-medium">{{ authStore.user?.username || 'Usuario' }}</span>
          </div>
          <button @click="authStore.logout" class="btn-outline">Salir</button>
        </div>
        <div v-else class="space-x-2">
      <router-link to="/login" class="btn-gold">Iniciar Sesión</router-link>
      <router-link to="/register" class="btn-outline">Registrarse</router-link>
        </div>
      </div>
    <div class="h-1 bg-gradient-to-r from-gold-500/60 via-emerald-500/30 to-navy-700/50"></div>
    </nav>

    <main class="container mx-auto p-4 pt-6 md:pt-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import logoUrl from './public/img/Logo.png'

const authStore = useAuthStore()

// Cargar la información del usuario al iniciar la aplicación si está autenticado
onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    try {
      await authStore.getCurrentUser()
    } catch (error) {
      console.error('Error loading user on app mount:', error)
    }
  }
})
</script>

<style scoped>
:root {
  --green: #10b981;        /* emerald-500 */
  --green-dark: #065f46;   /* emerald-900 */
  --lime: #a3e635;         /* lime-400 */
}

.nav-link {
  color: rgba(209, 250, 229, 0.9);
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  transition: color .15s ease-in-out, background-color .15s ease-in-out;
}
.nav-link:hover { color: #bef264; }
.btn {
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  background: #059669;
  color: #fff;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background .15s ease-in-out;
}
.btn:hover { background: #047857; }
.btn-outline {
  display: inline-flex;
  align-items: center;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid rgba(16, 185, 129, 0.6);
  color: #cceee4;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background .15s ease-in-out, color .15s ease-in-out, border-color .15s ease-in-out;
}
.btn-outline:hover { background: rgba(4, 120, 87, 0.3); }
</style>
