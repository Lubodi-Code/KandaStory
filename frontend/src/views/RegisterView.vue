<template>
  <div class="max-w-md mx-auto">
  <h1 class="text-2xl font-bold mb-6 text-center text-gold-400">Registrarse</h1>
    
  <form @submit.prevent="handleRegister" class="card-navy card-accent p-6 rounded-lg shadow-xl">
      <div class="mb-4">
        <label for="username" class="block text-sm font-medium text-emerald-200 mb-2">
          Nombre de usuario
        </label>
        <input
          id="username"
          v-model="username"
          type="text"
          required
          class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100 placeholder:text-slate-400"
          placeholder="Ej: johndoe"
        />
      </div>
      
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
          placeholder="tu@email.com"
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
          placeholder="Mínimo 6 caracteres"
        />
      </div>
      
      <button
        type="submit"
        :disabled="loading"
        class="w-full btn-gold disabled:opacity-50"
      >
        {{ loading ? 'Registrando...' : 'Registrarse' }}
      </button>
      
      <div v-if="error" class="mt-4 text-rose-400 text-sm text-center">
        {{ error }}
      </div>
      
      <div v-if="success" class="mt-4 text-emerald-300 text-sm text-center p-3 bg-navy-900/30 border border-emerald-800 rounded-md">
        <div class="font-medium mb-2">{{ success }}</div>
        <div class="text-sm text-slate-300">
          Revisa tu bandeja de entrada y haz clic en el enlace de verificación.
        </div>
        <button 
          @click="resendEmail" 
          :disabled="resendCooldown > 0"
          class="mt-2 text-emerald-200 hover:text-emerald-100 underline disabled:opacity-50"
        >
          {{ resendCooldown > 0 ? `Reenviar en ${resendCooldown}s` : 'Reenviar email' }}
        </button>
      </div>
      
      <div class="mt-4 text-center">
        <router-link to="/login" class="text-emerald-300 hover:text-emerald-200 hover:underline">
          ¿Ya tienes cuenta? Inicia sesión
        </router-link>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const resendCooldown = ref(0)

async function handleRegister() {
  loading.value = true
  error.value = ''
  success.value = ''
  
  try {
    const response = await authStore.register(username.value, email.value, password.value)
    success.value = response.message || 'Registro exitoso. Verifica tu email para activar tu cuenta.'
    
    // Clear form except email (needed for resend)
    username.value = ''
    password.value = ''
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error al registrarse'
  } finally {
    loading.value = false
  }
}

async function resendEmail() {
  if (resendCooldown.value > 0 || !email.value) return
  
  try {
    await authStore.resendVerification(email.value)
    success.value = 'Email de verificación reenviado. Revisa tu bandeja de entrada.'
    
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

