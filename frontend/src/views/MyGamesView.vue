<template>
  <div class="max-w-4xl mx-auto p-4">
  <h1 class="text-4xl md:text-5xl font-extrabold mb-6 text-gold-400 tracking-tight leading-tight">Mis partidas</h1>
    <div v-if="loading" class="text-center py-8">
      <div class="text-slate-100 text-xl font-medium">Cargando partidas...</div>
    </div>
    <div v-else>
      <!-- Filtros -->
      <div class="flex items-center gap-3 mb-4">
        <button :class="['px-3 py-1 rounded-full font-semibold', filter === 'all' ? 'bg-emerald-600 text-white' : 'bg-white/5 text-emerald-200']" @click="filter = 'all'">Todas</button>
        <button :class="['px-3 py-1 rounded-full font-semibold', filter === 'active' ? 'bg-emerald-600 text-white' : 'bg-white/5 text-emerald-200']" @click="filter = 'active'">En curso</button>
        <button :class="['px-3 py-1 rounded-full font-semibold', filter === 'finished' ? 'bg-emerald-600 text-white' : 'bg-white/5 text-emerald-200']" @click="filter = 'finished'">Finalizadas</button>
      </div>

      <div v-if="filteredGames.length === 0" class="text-center py-8">
        <div class="text-slate-100 mb-4 text-xl font-medium">No hay partidas en esta categoría</div>
        <router-link to="/rooms" class="btn-gold">Explorar salas</router-link>
      </div>

      <div v-else class="grid gap-3">
        <div 
          v-for="game in filteredGames" 
          :key="game._id" 
          class="p-8 card-navy border-emerald-800 rounded-lg flex justify-between items-center hover:card-accent transition-all shadow-lg text-slate-100"
        >
          <div>
            <div class="font-bold text-3xl md:text-4xl text-emerald-50 leading-snug">{{ game.name || 'Partida' }}</div>
            <div class="text-base md:text-lg text-slate-200 mt-3 leading-relaxed">
              <span class="mr-2 opacity-90">Capítulo</span>
              <span class="inline-flex items-center font-semibold text-emerald-200 text-lg md:text-xl ml-2 px-3 py-1 bg-emerald-900/50 rounded">
                {{ game.current_chapter || 1 }}
              </span>
              <span v-if="game.game_state" class="ml-2 px-2 py-1 rounded text-xs bg-emerald-900/30 text-emerald-200">
                {{ game.game_state === 'finished' ? 'Finalizada' : (game.game_state === 'playing' ? 'En curso' : 'Pausada') }}
              </span>
            </div>
            <div v-if="game.created_at" class="text-sm text-slate-300 mt-2">
              Creada {{ formatDate(game.created_at) }}
            </div>
          </div>
          <button 
            class="btn-gold px-6 py-3 text-lg"
            @click="openGame(game._id)"
          >
            Entrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../lib/api'

const router = useRouter()
const loading = ref(true)
const games = ref<any[]>([])

// filtro UI: 'all' | 'active' | 'finished'
const filter = ref<'all'|'active'|'finished'>('all')

import { computed } from 'vue'

const filteredGames = computed(() => {
  // copiar lista y ordenar por fecha descendente (más reciente primero)
  const arr = (games.value || []).slice().sort((a: any, b: any) => {
    const da = a.created_at ? new Date(a.created_at).getTime() : 0
    const db = b.created_at ? new Date(b.created_at).getTime() : 0
    return db - da
  })

  if (filter.value === 'all') return arr
  if (filter.value === 'active') return arr.filter((g: any) => g.game_state === 'playing' || g.game_state === 'action_phase')
  return arr.filter((g: any) => g.game_state === 'finished' || g.finished === true)
})

async function loadGames() {
  try {
    const { data } = await apiClient.get('/games/my')
    games.value = data || []
  } catch (error: any) {
    console.error('Error cargando partidas:', error)
    if (error.response?.status === 401) {
      router.push('/login')
    }
  } finally {
    loading.value = false
  }
}

function openGame(gameId: string) {
  router.push({ name: 'game', params: { id: gameId } })
}

function formatDate(dateStr: string) {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('es-ES', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    })
  } catch {
    return 'Fecha desconocida'
  }
}

onMounted(loadGames)
</script>
