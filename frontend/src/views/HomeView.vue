<template>
  <div class="max-w-2xl mx-auto">
  <h1 class="text-3xl font-bold mb-8 text-center text-gold-400">Bienvenido a KandaStory</h1>
    
    <div class="card-navy p-6 rounded-lg shadow-xl border card-accent">
      <h2 class="text-xl font-semibold mb-4 text-emerald-200">¡Crea tu primera aventura!</h2>
      <p class="text-slate-300 mb-4">
        En KandaStory puedes crear personajes únicos con IA, unirte a salas de aventuras 
        y vivir historias generadas colaborativamente.
      </p>
      
      <div class="space-y-4">
    <div v-if="!authStore.isAuthenticated" class="text-center">
          <router-link 
            to="/register" 
      class="btn-gold mr-4"
          >
            Comenzar
          </router-link>
          <router-link 
            to="/login" 
            class="btn-outline"
          >
            Ya tengo cuenta
          </router-link>
        </div>
        
        <div v-else class="text-center">
          <router-link 
            to="/characters" 
            class="btn mr-4"
          >
            Mis Personajes
          </router-link>
          <router-link 
            to="/rooms" 
            class="btn-outline"
          >
            Salas de Aventura
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
</script>
