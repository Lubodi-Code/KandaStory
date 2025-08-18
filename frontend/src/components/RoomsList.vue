<template>
  <div>
    <!-- Loading state -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400"></div>
      <p class="mt-2 text-slate-300">Cargando salas...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-rose-900/20 border border-rose-800 rounded-lg p-4 mb-6">
      <p class="text-rose-300">Error: {{ error }}</p>
      <button @click="$emit('reload')" class="mt-2 text-rose-200 underline hover:text-rose-100">Reintentar</button>
    </div>

    <!-- Rooms grid -->
    <div v-else-if="rooms.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="room in rooms" 
        :key="room._id"
        class="card-navy border rounded-lg shadow-xl overflow-hidden hover:shadow-2xl hover:border-emerald-700 transition-all"
      >
        <div class="p-6">
          <!-- Header -->
          <div class="flex justify-between items-start mb-3 header">
            <h3 class="font-semibold text-lg text-gold-300 truncate">{{ room.name }}</h3>
            <span class="text-xs px-2 py-1 rounded bg-navy-800 text-emerald-200 border border-emerald-700">
              {{ getStateText(room.game_state) }}
            </span>
          </div>

          <!-- World info -->
          <p v-if="room.world" class="text-slate-300 text-sm mb-3">
            {{ room.world.title }} - {{ room.world.time_period }}
          </p>
          <p v-else class="text-slate-400 text-sm mb-3">Sin mundo asignado</p>

          <!-- Room stats -->
          <div class="flex justify-between items-center text-sm text-slate-300 mb-4">
            <span>{{ room.current_members || 0 }}/{{ room.max_players }} jugadores</span>
            <span v-if="room.is_user_member" class="text-emerald-300 font-medium">
              ✓ Miembro
            </span>
          </div>

          <!-- Actions -->
          <div class="flex space-x-2">
            <!-- Si ya es miembro -->
            <template v-if="room.is_user_member">
              <button 
                v-if="room.game_state === 'playing' && room.game_id"
                @click="$emit('goToGame', room.game_id)"
                class="flex-1 btn text-sm"
              >
                🎮 Jugar
              </button>
              <button 
                v-else
                @click="$emit('goToRoom', room._id)"
                class="flex-1 btn-outline text-sm"
              >
                Ver Sala
              </button>
            </template>
            
            <!-- Si no es miembro pero puede unirse -->
            <button 
              v-else-if="room.is_joinable"
              @click="$emit('joinRoom', room._id)"
              :disabled="joining === room._id"
              class="flex-1 btn text-sm disabled:opacity-50"
            >
              {{ joining === room._id ? 'Uniéndose...' : 'Unirse' }}
            </button>
            
            <!-- Si no puede unirse -->
            <button 
              v-else
              disabled
              class="flex-1 bg-gray-600 text-slate-300 py-2 px-3 rounded text-sm cursor-not-allowed opacity-50"
            >
              {{ room.game_state === 'playing' ? 'En juego' : 'Llena' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-12">
      <div class="text-gold-400 text-6xl mb-4">🏰</div>
  <h3 class="text-xl font-semibold text-gold-300 mb-2">No hay salas disponibles</h3>
      <p class="text-slate-300 mb-4">¡Sé el primero en crear una aventura!</p>
      <div class="flex gap-3 justify-center">
        <button
          @click="$emit('openCreate')"
          class="btn-gold"
        >
          ✨ Crear primera sala
        </button>
        
        <!-- opcional: acceso a mundos si no hay ninguno -->
        <router-link
          v-if="!hasWorlds"
          to="/worlds"
          class="px-6 py-3 border rounded-lg hover:bg-navy-800 border-emerald-700 text-emerald-200"
        >
          Crear un mundo
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Room {
  _id: string
  name: string
  world?: {
    title: string
    time_period: string
  }
  current_members: number
  max_players: number
  game_state: string
  is_user_member: boolean
  is_joinable: boolean
  game_id?: string
}

defineProps<{
  rooms: Room[]
  loading: boolean
  error: string | null
  joining: string | null
  hasWorlds: boolean
}>()

defineEmits<{
  reload: []
  goToRoom: [roomId: string]
  goToGame: [gameId: string]
  joinRoom: [roomId: string]
  openCreate: []
}>()

// State helpers
function getStateText(state: string): string {
  switch (state) {
    case 'waiting': return 'Esperando'
    case 'character_selection': return 'Personajes'
    case 'playing': return 'En juego'
    case 'discussion': return 'Discusión'
    case 'finished': return 'Terminado'
    default: return 'Desconocido'
  }
}

function getStateColor(state: string): string {
  switch (state) {
    case 'waiting': return 'bg-yellow-100 text-yellow-800'
    case 'character_selection': return 'bg-blue-100 text-blue-800'
    case 'playing': return 'bg-green-100 text-green-800'
    case 'discussion': return 'bg-purple-100 text-purple-800'
    case 'finished': return 'bg-gray-100 text-gray-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}
</script>
