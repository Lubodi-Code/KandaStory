<template>
  <div class="max-w-md mx-auto">
  <div class="card-navy card-accent p-6 rounded-lg shadow-xl text-center">
      <!-- Loading state -->
      <div v-if="loading" class="py-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto mb-4"></div>
        <p class="text-slate-300">Verificando tu email...</p>
      </div>

      <!-- Success state -->
      <div v-else-if="success" class="py-8">
  <div class="text-gold-300 text-6xl mb-4">✓</div>
  <h1 class="text-2xl font-bold text-gold-400 mb-4">¡Email verificado exitosamente!</h1>
        <p class="text-slate-300 mb-4">Tu cuenta ha sido activada y has iniciado sesión automáticamente.</p>
        <p class="text-sm text-emerald-300 font-medium mb-6">¡Bienvenido a KandaStory!</p>
        <div class="space-y-3">
          <router-link 
            to="/" 
            class="btn-gold inline-block"
          >
            Ir al inicio
          </router-link>
          <br>
          <router-link 
            to="/characters" 
            class="btn-outline inline-block"
          >
            Explorar personajes
          </router-link>
        </div>
      </div>

      <!-- Error state -->
      <div v-else class="py-8">
        <div class="text-rose-400 text-6xl mb-4">✗</div>
        <h1 class="text-2xl font-bold text-rose-400 mb-4">Error de verificación</h1>
        <p class="text-slate-300 mb-6">{{ error }}</p>
        <div class="space-y-3">
          <router-link 
            to="/register" 
            class="btn-gold inline-block mr-2"
          >
            Registrarse nuevamente
          </router-link>
          <router-link 
            to="/login" 
            class="btn-outline inline-block"
          >
            Ir al login
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const success = ref(false)
const error = ref('')

onMounted(async () => {
  const token = route.query.token as string
  
  if (!token) {
    error.value = 'Token de verificación no encontrado.'
    loading.value = false
    return
  }

  try {
    await authStore.verifyEmail(token)
    success.value = true
    
    // Show success message for 3 seconds then redirect to home
    setTimeout(() => {
      router.push('/')
    }, 3000)
    
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Token inválido o expirado.'
  } finally {
    loading.value = false
  }
})
</script>
