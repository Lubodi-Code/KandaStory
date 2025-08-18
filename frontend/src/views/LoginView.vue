<template>
  <div class="max-w-md mx-auto">
  <h1 class="text-2xl font-bold mb-6 text-center text-gold-400">Iniciar Sesión</h1>
    
  <form @submit.prevent="handleLogin" class="card-navy card-accent p-6 rounded-lg shadow-xl">
      <div class="mb-4">
        <label for="email" class="block text-sm font-medium text-emerald-200 mb-2">
          Email
        </label>
        <input
          id="email"
          v-model="email"
          type="email"
          required
          class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100 placeholder:text-slate-400"
        />
      </div>
      
      <div class="mb-6">
        <label for="password" class="block text-sm font-medium text-emerald-200 mb-2">
          Contraseña
        </label>
        <input
          id="password"
          v-model="password"
          type="password"
          required
          class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100 placeholder:text-slate-400"
        />
      </div>
      
      <button
        type="submit"
        :disabled="loading"
        class="w-full btn-gold disabled:opacity-50"
      >
        {{ loading ? 'Iniciando...' : 'Iniciar Sesión' }}
      </button>
      
      <div v-if="error" class="mt-4 text-rose-400 text-sm text-center">
        {{ error }}
        <div v-if="showResendOption" class="mt-2">
          <button 
            @click="resendVerification" 
            :disabled="resendCooldown > 0"
            class="text-emerald-300 hover:text-emerald-200 underline disabled:opacity-50"
          >
            {{ resendCooldown > 0 ? `Reenviar en ${resendCooldown}s` : 'Reenviar email de verificación' }}
          </button>
        </div>
      </div>
      
      <div class="mt-4 text-center">
        <router-link to="/register" class="text-emerald-300 hover:text-emerald-200 hover:underline">
          ¿No tienes cuenta? Regístrate
        </router-link>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const resendCooldown = ref(0)

const showResendOption = computed(() => 
  error.value.includes('no verificado') || error.value.includes('not verified')
)

async function handleLogin() {
  loading.value = true
  error.value = ''
  
  try {
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error al iniciar sesión'
  } finally {
    loading.value = false
  }
}

async function resendVerification() {
  if (resendCooldown.value > 0 || !email.value) return
  
  try {
    await authStore.resendVerification(email.value)
    error.value = 'Email de verificación reenviado. Revisa tu bandeja de entrada.'
    
    // Start cooldown
    resendCooldown.value = 60
    const interval = setInterval(() => {
      resendCooldown.value--
      if (resendCooldown.value <= 0) {
        clearInterval(interval)
      }
    }, 1000)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error al reenviar email'
  }
}
</script>
