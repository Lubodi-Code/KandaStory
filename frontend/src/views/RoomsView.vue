<template>
  <div class="max-w-6xl mx-auto p-4 app-noise">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-3xl font-bold text-gold-400">Salas de Aventura</h1>
      <div class="flex space-x-4">
        <button @click="showCreateForm = true" class="btn-gold">✨ Crear Sala</button>
        <button @click="loadRooms" :disabled="loading" class="btn-outline">🔄 Actualizar</button>
      </div>
    </div>

    <!-- Mi sala actual -->
    <div v-if="userRoom && userRoom._id" class="bg-neutral-900/70 rounded-xl shadow-lg p-6 mb-6 border border-emerald-700/20">
      <h2 class="text-xl font-semibold mb-3 text-emerald-50">Mi Sala Actual</h2>
      <div class="flex justify-between items-center">
        <div>
          <h3 class="font-medium text-lg">{{ userRoom.name }}</h3>
          <p class="text-emerald-100">{{ userRoom.world?.title || 'Mundo desconocido' }}</p>
          <div class="flex items-center space-x-4 mt-2 text-sm text-gray-500">
            <span>{{ userRoom.current_members || 0 }}/{{ userRoom.max_players }} jugadores</span>
            <span class="px-2 py-1 rounded text-xs" :class="getStateColor(userRoom.game_state)">
              {{ getStateText(userRoom.game_state) }}
            </span>
          </div>
        </div>
        <div class="flex space-x-2">
          <button
            v-if="userRoom.game_state === 'playing' && userRoom.game_id"
            @click="goToGame(userRoom.game_id)"
            class="btn-gold"
          >
            🎮 Continuar Juego
          </button>
          <button @click="goToRoom(userRoom._id)" class="btn-outline">Ver Sala</button>
        </div>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-gray-600">Cargando salas...</p>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <p class="text-red-800">Error: {{ error }}</p>
      <button @click="loadRooms" class="mt-2 text-red-600 underline">Reintentar</button>
    </div>

    <!-- Rooms grid -->
    <div v-else-if="rooms.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="room in rooms"
        :key="room._id"
        class="bg-gradient-to-br from-neutral-800/90 to-neutral-900/80 rounded-2xl shadow-xl overflow-hidden transform transition hover:shadow-2xl hover:-translate-y-1 border border-emerald-700/10"
      >
        <div class="p-6">
          <!-- Header -->
          <div class="flex justify-between items-start mb-3">
            <h3 class="font-semibold text-lg text-emerald-50 truncate">{{ room.name }}</h3>
            <span class="text-xs px-3 py-1 rounded-full" :class="getStateColor(room.game_state)">
              {{ getStateText(room.game_state) }}
            </span>
          </div>

          <!-- World info -->
          <p v-if="room.world" class="text-emerald-100 text-sm mb-3">
            {{ room.world.title }} - {{ room.world.time_period }}
          </p>
          <p v-else class="text-emerald-200 text-sm mb-3">Sin mundo asignado</p>

          <!-- Room stats -->
          <div class="flex justify-between items-center text-sm text-emerald-200 mb-4">
            <span>{{ room.current_members || 0 }}/{{ room.max_players }} jugadores</span>
            <span v-if="room.is_user_member" class="text-emerald-300 font-medium">✓ Miembro</span>
          </div>

          <!-- Actions -->
          <div class="flex space-x-2">
            <!-- Si ya es miembro -->
            <template v-if="room.is_user_member">
              <div class="flex-1 flex space-x-2">
                <button
                  v-if="room.game_state === 'playing' && room.game_id"
                  @click="goToGame(room.game_id)"
                  class="flex-1 btn-gold py-2 px-3 text-sm"
                >
                  🎮 Jugar
                </button>

                <template v-else>
                  <!-- Mostrar “Listo” si soy miembro y la sala está esperando (sin depender de is_joinable) -->
                  <button
                    v-if="room.game_state === 'waiting'"
                    @click.prevent="toggleReadyWS(room)"
                    :disabled="toggling === room._id"
                    :class="['flex-1 py-2 px-3 text-sm', isReady(room) ? 'btn-gold' : 'btn-outline', toggling === room._id ? 'opacity-60 cursor-wait' : '']"
                  >
                    {{ toggling === room._id ? 'Enviando...' : (isReady(room) ? 'Cancelar listo' : 'Listo') }}
                  </button>

                  <button @click="goToRoom(room._id)" class="flex-1 btn-outline py-2 px-3 text-sm">
                    Ver Sala
                  </button>
                </template>
              </div>
            </template>

            <!-- Si no es miembro pero puede unirse -->
            <button
              v-else-if="room.is_joinable"
              @click="joinRoom(room._id)"
              :disabled="joining === room._id"
              class="flex-1 btn-gold py-2 px-3 text-sm disabled:opacity-60"
            >
              {{ joining === room._id ? 'Uniéndose...' : 'Unirse' }}
            </button>

            <!-- Si no puede unirse -->
            <button
              v-else
              disabled
              class="flex-1 bg-gray-600 text-white py-2 px-3 rounded text-sm cursor-not-allowed disabled:opacity-60"
            >
              {{ room.game_state === 'playing' ? 'En juego' : 'Llena' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-12">
      <div class="text-gray-400 text-6xl mb-4">🏰</div>
      <h3 class="text-xl font-semibold text-gold-300 mb-2">No hay salas disponibles</h3>
      <p class="text-slate-400 mb-4">¡Sé el primero en crear una aventura!</p>
      <button @click="showCreateForm = true" class="btn-gold px-6 py-3 rounded-lg">✨ Crear Primera Sala</button>
    </div>

    <!-- Create Room Modal -->
    <CreateRoomForm :show="showCreateForm" @close="showCreateForm = false" @created="onRoomCreated" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../lib/api'
import CreateRoomForm from '../components/CreateRoomForm.vue'

const router = useRouter()

const showCreateForm = ref(false)

function onRoomCreated(roomId: string) {
  showCreateForm.value = false
  if (roomId) router.push(`/rooms/${roomId}`)
}

interface Room {
  _id: string
  name: string
  world?: { title: string; time_period: string }
  current_members: number
  max_players: number
  game_state: string
  is_user_member: boolean
  is_joinable: boolean
  game_id?: string
  ready_players?: string[]
}

const rooms = ref<Room[]>([])
const userRoom = ref<Room | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const joining = ref<string | null>(null)
const toggling = ref<string | null>(null)

// current user id (local) to compute ready state
const currentUserId = ref<string>('')
try {
  const saved = localStorage.getItem('user')
  if (saved) {
    const parsed = JSON.parse(saved)
    currentUserId.value = String(parsed?.id || parsed?._id || '')
  }
} catch {}

// === Helpers de estado ===
function isReady(room: Room): boolean {
  return !!(room.ready_players || []).includes(currentUserId.value)
}

// === WebSocket (efímero) para toggle_ready ===
function getAccessToken(): string | null {
  // Ajusta estos keys según tu auth real
  const direct = localStorage.getItem('access_token') || localStorage.getItem('token')
  if (direct) return direct
  try {
    const auth = JSON.parse(localStorage.getItem('auth') || 'null')
    return auth?.token || null
  } catch {
    return null
  }
}

function buildWSUrl(path: string): string {
  const base =
    import.meta.env.VITE_WS_BASE ||
    (window.location.origin.startsWith('https')
      ? window.location.origin.replace('https', 'wss')
      : window.location.origin.replace('http', 'ws'))
  // Asegurar que no hay doble slash
  return `${base.replace(/\/$/, '')}${path.startsWith('/') ? path : `/${path}`}`
}

async function toggleReadyWS(room: Room) {
  if (!currentUserId.value) {
    error.value = 'Usuario no autenticado'
    return
  }

  const token = getAccessToken()
  if (!token) {
    error.value = 'No se encontró token de autenticación'
    return
  }

  toggling.value = room._id

  // Optimistic update
  room.ready_players = room.ready_players || []
  const idx = room.ready_players.indexOf(currentUserId.value)
  if (idx >= 0) room.ready_players.splice(idx, 1)
  else room.ready_players.push(currentUserId.value)

  // WS efímero: /ws/{room_id}?token=...
  const url = buildWSUrl(`/ws/${room._id}?token=${encodeURIComponent(token)}`)
  let ws: WebSocket | null = null

  try {
    ws = new WebSocket(url)

    // Cuando abra, enviar toggle_ready
    ws.onopen = () => {
      try {
        ws?.send(JSON.stringify({ type: 'toggle_ready' }))
        // Cerrar poco después para no mantener conexiones desde la grilla
        setTimeout(() => ws?.close(), 250)
      } catch {
        /* noop */
      }
    }

    ws.onerror = () => {
      // Revertir optimistic update si hay error
      const i = room.ready_players!.indexOf(currentUserId.value)
      if (i >= 0 && !isReady(room)) {
        // ya estaba listo y falló la cancelación -> vuelve a estar listo
        room.ready_players!.push(currentUserId.value)
      } else if (i >= 0 && isReady(room)) {
        // nada
      }
      error.value = 'No se pudo enviar el estado de listo'
    }
  } catch (e: any) {
    // Revertir optimistic en fallo de construcción
    const i = room.ready_players!.indexOf(currentUserId.value)
    if (i >= 0) room.ready_players!.splice(i, 1)
    error.value = e?.message || 'Error al cambiar estado listo'
  } finally {
    setTimeout(() => {
      toggling.value = null
    }, 200)
  }
}

// === Utilidades ===
function isValidObjectId(id: string): boolean {
  if (!id || typeof id !== 'string') return false
  return /^[0-9a-fA-F]{24}$/.test(id)
}

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

// === Navegación ===
function goToRoom(roomId: string) {
  if (!isValidObjectId(roomId)) {
    console.error('Invalid room ID:', roomId)
    error.value = 'ID de sala inválido'
    return
  }
  router.push(`/rooms/${roomId}`)
}

function goToGame(gameId: string) {
  if (!isValidObjectId(gameId)) {
    console.error('Invalid game ID:', gameId)
    error.value = 'ID de juego inválido'
    return
  }
  router.push(`/game/${gameId}`)
}

// === API ===
async function loadRooms() {
  loading.value = true
  error.value = null
  try {
    const { data } = await apiClient.get('/rooms/public')
    rooms.value = data?.rooms || data || []

    // Mi sala actual (si existe)
    try {
      const { data: userRoomData } = await apiClient.get('/rooms/my-room')
      userRoom.value = userRoomData
    } catch {
      userRoom.value = null
    }
  } catch (err: any) {
    console.error('Error loading rooms:', err)
    error.value = err?.response?.data?.detail || 'Error al cargar las salas'
  } finally {
    loading.value = false
  }
}

async function joinRoom(roomId: string) {
  if (!isValidObjectId(roomId)) {
    error.value = 'ID de sala inválido'
    return
  }
  joining.value = roomId
  try {
    await apiClient.post(`/rooms/${roomId}/join`)
    router.push(`/rooms/${roomId}`)
  } catch (err: any) {
    console.error('Error joining room:', err)
    // Redirigir si la sala fue cerrada y el backend devuelve 410 con redirect_game_id
    if (err?.response?.status === 410) {
      const gid = err?.response?.data?.redirect_game_id
      if (gid && isValidObjectId(gid)) {
        router.replace({ name: 'game', params: { id: gid } })
        return
      }
    }
    error.value = err?.response?.data?.detail || 'Error al unirse a la sala'
  } finally {
    joining.value = null
  }
}

// === Lifecycle ===
onMounted(() => {
  loadRooms()
})
</script>
