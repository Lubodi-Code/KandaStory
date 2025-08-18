<template>
  <div v-if="room" class="min-h-screen p-4">
    <!-- Header de la sala -->
  <div class="card-navy card-accent rounded-lg shadow-xl p-6 mb-6">
      <div class="flex justify-between items-center">
        <div>
      <h1 class="text-2xl font-bold text-gold-400">{{ room.name }}</h1>
      <p class="text-slate-300" v-if="room.world">{{ room.world.title }} - {{ room.world.time_period }}</p>
          <p v-if="(room as any).game_id" class="mt-1 text-xs text-slate-400 select-all">
            Game ID: {{ (room as any).game_id }}
          </p>
        </div>
        <div class="flex items-center space-x-4">
          <span class="text-sm px-3 py-1 rounded-full bg-navy-900/30 text-emerald-200" :class="gameStateColor">
            {{ gameStateText }}
          </span>
          <button
            @click="leaveRoom"
            class="btn-outline"
          >
            Salir de la Sala
          </button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Columna izquierda: Miembros -->
      <div class="lg:col-span-1 card-navy rounded-lg shadow-xl p-4">
  <h3 class="text-lg font-semibold mb-4 text-gold-400">Miembros ({{ room.members?.length || 0 }}/{{ room.max_players }})</h3>
        <div class="space-y-2">
          <div
            v-for="member in room.members"
            :key="member.user_id"
            class="flex items-center justify-between p-2 bg-navy-900/40 border border-emerald-800 rounded"
          >
            <div class="flex items-center space-x-2">
              <div
                class="w-2 h-2 rounded-full"
                :class="member.is_ready ? 'bg-emerald-400' : 'bg-slate-400'"
              ></div>
              <span class="text-sm font-medium text-slate-100">{{ member.username }}</span>
              <span
                v-if="member.user_id === room.admin_id"
                class="text-xs bg-emerald-900/30 text-emerald-200 px-2 py-1 rounded"
              >
                Admin
              </span>
            </div>
          </div>
        </div>

        <!-- Botón de listo -->
          <div class="mt-4" v-if="room.game_state === 'waiting'">
          <button
            @click="toggleReady"
            :disabled="!hasSelectedCharacterForCurrentUser"
            :class="[
              isUserReady ? 'bg-gold-400 text-navy-900 font-bold shadow-lg hover:bg-gold-300' : 'bg-gold-300/90 text-navy-900 font-semibold shadow-md hover:bg-gold-300/95',
              !hasSelectedCharacterForCurrentUser ? 'opacity-50 cursor-not-allowed' : ''
            ]"
            class="w-full py-3 rounded-md"
          >
            <span v-if="isUserReady">✓ Listo</span>
            <span v-else>Marcar como Listo</span>
          </button>
          <p v-if="!hasSelectedCharacterForCurrentUser" class="text-xs text-rose-400 mt-2 text-center">
            Debes seleccionar un personaje antes de marcarte como listo.
          </p>
          <p class="text-xs text-slate-400 mt-2 text-center">
            {{ readyCount }}/{{ totalMembers }} jugadores listos
          </p>

          <!-- Botón de iniciar juego (solo admin) -->
          <div v-if="isStartingGame" class="mt-4 text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-400 mx-auto mb-2"></div>
            <p class="text-sm text-gold-300">Iniciando la partida...</p>
            <p class="text-xs text-slate-400">Por favor espera un momento</p>
          </div>
          <div v-else-if="isAdmin && canStartGame" class="mt-4">
            <button
              @click="startGame"
              class="w-full btn-gold font-medium"
            >
              🎮 Iniciar Juego
            </button>
            <p class="text-xs text-emerald-300 mt-1 text-center">¡Todos listos! Puedes iniciar la aventura</p>
          </div>
        </div>
      </div>

      <!-- Columna central: Historia y Chat -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Historia -->
        <div class="card-navy rounded-lg shadow-md p-6" v-if="room.chapters?.length > 0">
          <h3 class="text-lg font-semibold mb-4 text-gold-300">Historia - Capítulo {{ room.current_chapter }}</h3>
          <div class="prose max-w-none">
            <div v-for="(chapter, index) in room.chapters" :key="index" class="mb-6">
              <h4 class="text-md font-medium text-emerald-200 mb-2">Capítulo {{ index + 1 }}</h4>
              <p class="text-slate-200 leading-relaxed whitespace-pre-wrap">{{ chapter }}</p>
            </div>
          </div>
        </div>

        <!-- Estado de espera -->
        <div class="card-navy rounded-lg shadow-md p-6" v-else-if="room.game_state === 'waiting'">
          <h3 class="text-lg font-semibold mb-4 text-gold-300">Esperando jugadores...</h3>
          <p class="text-slate-300">
            Todos los jugadores deben seleccionar un personaje y marcar "Listo" para comenzar la aventura.
          </p>
        </div>

        <!-- Chat -->
        <div class="card-navy rounded-lg shadow-md p-4">
          <h3 class="text-lg font-semibold mb-4 text-gold-300">Chat</h3>

          <!-- Mensajes -->
          <div class="h-64 overflow-y-auto rounded p-3 mb-4 bg-navy-900/30 border border-emerald-800" ref="chatContainer">
            <div
              v-for="(message, index) in room.messages"
              :key="index"
              class="mb-2 p-2 rounded"
              :class="message.message_type === 'action' ? 'bg-navy-900/50 border-l-4 border-gold-400 text-emerald-100' : 'bg-navy-900/40 text-slate-100'"
            >
              <div class="flex items-center space-x-2 mb-1">
                <span class="text-xs font-medium text-emerald-200">{{ message.username }}</span>
                <span class="text-xs text-slate-400">{{ formatTime(message.timestamp) }}</span>
                <span
                  v-if="message.message_type === 'action'"
                  class="text-xs bg-gold-400/20 text-gold-300 px-2 py-1 rounded"
                >
                  Acción
                </span>
              </div>
              <p class="text-sm">{{ message.message }}</p>
            </div>
          </div>

          <!-- Enviar mensaje -->
          <form @submit.prevent="sendMessage" class="flex space-x-2">
            <input
              v-model="newMessage"
              type="text"
              placeholder="Escribe un mensaje..."
              class="flex-1 px-3 py-2 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-navy-900/40 text-white placeholder:text-zinc-400"
            />
            <button type="submit" class="btn-gold px-4 py-2">
              Enviar
            </button>
          </form>

          <!-- Enviar acción (solo durante discusión) -->
          <div v-if="room.game_state === 'discussion'" class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded">
            <h4 class="font-medium text-yellow-800 mb-2">Propón una acción para tu personaje:</h4>
            <form @submit.prevent="sendAction" class="flex space-x-2">
              <input
                v-model="newAction"
                type="text"
                placeholder="Describe qué quiere hacer tu personaje..."
                class="flex-1 px-3 py-2 border border-yellow-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-500"
              />
              <button type="submit" class="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700">
                Enviar Acción
              </button>
            </form>
          </div>
        </div>
      </div>

      <!-- Columna derecha: Personajes -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Tooltip -->
        <div
          v-if="tooltipCharacter && showTooltipFlag"
          class="fixed z-50 bg-gray-800 text-white p-3 rounded-lg shadow-lg max-w-xs"
          :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
        >
          <h4 class="font-bold text-sm mb-1">{{ tooltipCharacter.name }}</h4>
          <p class="text-xs">{{ tooltipCharacter.background }}</p>
          <div v-if="tooltipCharacter.traits?.length" class="mt-2">
            <p class="text-xs font-semibold">Características:</p>
            <div class="flex flex-wrap gap-1 mt-1">
              <span
                v-for="trait in tooltipCharacter.traits"
                :key="trait"
                class="bg-gray-700 px-2 py-1 rounded text-xs"
              >
                {{ trait }}
              </span>
            </div>
          </div>
        </div>

        <!-- Modal selección -->
        <div
          v-if="characterToSelect"
          class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
        >
          <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 class="text-xl font-bold mb-4">{{ characterToSelect.name }}</h3>
            <div class="mb-4">
              <p class="text-gray-700 mb-3">{{ characterToSelect.background }}</p>
              <div v-if="characterToSelect.traits?.length" class="mb-3">
                <p class="text-sm font-semibold text-gray-700 mb-2">Características:</p>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="trait in characterToSelect.traits"
                    :key="trait"
                    class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm"
                  >
                    {{ trait }}
                  </span>
                </div>
              </div>
            </div>
            <div class="flex space-x-3">
              <button
                @click="selectThisCharacter"
                :class="selectedCharacterId === characterToSelect._id ? 'bg-green-600 hover:bg-green-700' : 'bg-blue-600 hover:bg-blue-700'"
                class="flex-1 text-white py-2 px-4 rounded font-medium"
              >
                {{ selectedCharacterId === characterToSelect._id ? 'Personaje Seleccionado' : 'Seleccionar Personaje' }}
              </button>
              <button @click="closeCharacterModal" class="bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400">
                Cancelar
              </button>
            </div>
          </div>
        </div>

        <!-- Character Details Modal -->
        <div
          v-if="detailedCharacter"
          class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
        >
          <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 class="text-xl font-bold mb-4">{{ detailedCharacter.name }}</h3>
            <div class="prose max-w-none">
              <p>{{ detailedCharacter.background }}</p>
            </div>
            <button @click="closeCharacterDetails" class="mt-6 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              Cerrar
            </button>
          </div>
        </div>

        <!-- Mis personajes -->
        <div class="card-navy rounded-lg shadow-md p-4" v-if="room.game_state === 'waiting'">
          <h3 class="text-lg font-semibold mb-4 text-gold-400">Mis Personajes</h3>
          <div class="space-y-3 max-h-64 overflow-y-auto">
              <div
                v-for="character in myCharacters"
                :key="character._id"
                class="relative p-4 rounded-lg cursor-pointer transition transform duration-200 bg-navy-900/20 border border-emerald-800"
                :class="selectedCharacterId === character._id ? 'ring-2 ring-emerald-400 bg-navy-900/60 shadow-lg scale-105' : 'hover:-translate-y-0.5 hover:scale-105 hover:shadow-lg'"
                @click="showCharacterOptions(character)"
                @mouseenter="showTooltip(character, $event)"
                @mouseleave="hideTooltip"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-semibold text-emerald-200">{{ character.name }}</div>
                    <div class="text-xs text-slate-300 mt-1">
                      {{ (character.background || '').substring(0, 70) }}{{ (character.background?.length || 0) > 70 ? '...' : '' }}
                    </div>
                  </div>
                  <div v-if="selectedCharacterId === character._id" class="ml-3">
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs bg-emerald-500 text-navy-900 font-semibold">✓ Seleccionado</span>
                  </div>
                </div>
              </div>
            </div>

            <router-link to="/characters" class="block mt-4 text-center bg-gold-400 text-navy-900 py-2 px-4 rounded hover:bg-gold-300 font-medium">
              Crear Nuevo Personaje
            </router-link>
        </div>

        <!-- Personajes seleccionados -->
        <div class="card-navy rounded-lg shadow-md p-4">
          <h3 class="text-lg font-semibold mb-4 text-gold-400">Personajes en Juego</h3>
          <div class="space-y-3">
            <div
              v-for="selected in room.selected_characters"
              :key="selected.user_id"
              class="p-3 bg-purple-50 border border-purple-200 rounded-lg"
            >
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <div class="font-medium text-sm text-purple-800 mb-1">{{ selected.character_name }}</div>
                  <div class="text-xs text-purple-600 mb-2">Jugador: {{ getUserName(selected.user_id) }}</div>
                  <div v-if="selected.character?.background" class="text-xs text-gray-600">
                    {{ (selected.character.background || '').substring(0, 80) }}{{ (selected.character.background?.length || 0) > 80 ? '...' : '' }}
                  </div>
                  <div v-if="selected.character?.traits?.length" class="flex flex-wrap gap-1 mt-2">
                    <span
                      v-for="trait in selected.character.traits.slice(0, 3)"
                      :key="trait"
                      class="bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs"
                    >
                      {{ trait }}
                    </span>
                    <span v-if="selected.character.traits.length > 3" class="text-purple-600 text-xs">
                      +{{ selected.character.traits.length - 3 }} más
                    </span>
                  </div>
                </div>
                <button @click="showCharacterDetails(selected.character)" class="text-xs text-purple-600 hover:text-purple-800 underline ml-2">
                  Ver Detalles
                </button>
              </div>
            </div>
          </div>

          <div v-if="!room.selected_characters?.length" class="text-center text-gray-500 py-8">
            <div class="text-gray-400 text-4xl mb-2">👥</div>
            <p class="text-sm">No hay personajes seleccionados aún</p>
            <p class="text-xs text-gray-400 mt-1">Los jugadores deben elegir sus personajes para comenzar</p>
          </div>
        </div>

        <!-- Configuración (solo admin) -->
        <div class="card-navy rounded-lg shadow-md p-4" v-if="isAdmin">
          <h3 class="text-lg font-semibold mb-4 text-gold-400">Configuración</h3>
          <div class="space-y-3 text-sm">
            <div>
              <label class="block text-emerald-200 mb-1">Tiempo de discusión (segundos)</label>
              <input
                v-model.number="room.discussion_time"
                type="number"
                min="30"
                max="600"
                @change="updateRoomSettings"
                class="w-full px-2 py-1 border border-emerald-800 rounded bg-navy-900/30 text-white"
              />
            </div>
            <div>
              <label class="block text-emerald-200 mb-1">Máximo de capítulos</label>
              <input
                v-model.number="room.max_chapters"
                type="number"
                min="1"
                max="20"
                @change="updateRoomSettings"
                class="w-full px-2 py-1 border border-emerald-800 rounded bg-navy-900/30 text-white"
              />
              <p class="text-xs text-slate-400 mt-1">Valor entre 1 y 20.</p>
            </div>
            <div>
              <label class="flex items-center space-x-2 text-emerald-200">
                <input v-model="room.auto_continue" type="checkbox" @change="updateRoomSettings" class="rounded" />
                <span>Continuar automáticamente</span>
              </label>
            </div>
            <div v-if="!room.auto_continue">
              <label class="block text-emerald-200 mb-1">Tiempo para continuar (segundos)</label>
              <input
                v-model.number="room.continue_time"
                type="number"
                min="10"
                max="300"
                @change="updateRoomSettings"
                class="w-full px-2 py-1 border border-emerald-800 rounded bg-navy-900/30 text-white"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="flex justify-center items-center min-h-screen">
    <p class="text-lg text-gray-600">Cargando sala...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../lib/api'

const route = useRoute()
const router = useRouter()
const roomId = (route.params.id as string) || ''

// helper de ObjectId
const isValidObjectId = (s: string) => /^[0-9a-fA-F]{24}$/.test(s)

interface Character {
  _id: string
  name: string
  background?: string
  traits?: string[]
}

interface Room {
  id: string
  name: string
  world?: any
  game_state: string
  member_ids: string[]
  members: any[]
  selected_characters: any[]
  chapters: string[]
  messages: any[]
  current_chapter: number
  admin_id: string
  max_players: number
  max_chapters?: number
  discussion_time: number
  auto_continue: boolean
  continue_time: number
  ready_players: string[]
}

const room = ref<Room | null>(null)
const myCharacters = ref<Character[]>([])
const selectedCharacterId = ref<string | null>(null)
const newMessage = ref('')
const newAction = ref('')

let __localUserId = ''
try {
  const saved = localStorage.getItem('user')
  if (saved) {
    const parsed = JSON.parse(saved)
    __localUserId = String(parsed?.id || parsed?._id || '')
  }
} catch {}
const currentUserId = ref(__localUserId)

// Tooltip
const tooltipCharacter = ref<Character | null>(null)
const showTooltipFlag = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)

// Modales
const characterToSelect = ref<Character | null>(null)
const detailedCharacter = ref<Character | null>(null)

const chatContainer = ref<HTMLElement>()
const readyCount = ref(0)
const totalMembers = ref(0)
const isStartingGame = ref(false)
const ws = ref<WebSocket | null>(null)
const isConnected = ref(false)
const shouldReconnect = ref(true)

/* ---------- Computeds ---------- */
const gameStateText = computed(() => {
  switch (room.value?.game_state) {
    case 'waiting': return 'Esperando jugadores'
    case 'character_selection': return 'Seleccionando personajes'
    case 'playing': return 'Jugando'
    case 'discussion': return 'Discusión de acciones'
    case 'finished': return 'Terminado'
    default: return 'Desconocido'
  }
})

const gameStateColor = computed(() => {
  switch (room.value?.game_state) {
    case 'waiting': return 'bg-yellow-100 text-yellow-800'
    case 'playing': return 'bg-green-100 text-green-800'
    case 'discussion': return 'bg-blue-100 text-blue-800'
    case 'finished': return 'bg-gray-100 text-gray-800'
    default: return 'bg-gray-100 text-gray-800'
  }
})

const isAdmin = computed(() => currentUserId.value === room.value?.admin_id)
const isUserReady = computed(() => room.value?.ready_players?.includes(currentUserId.value) || false)

const hasSelectedCharacterForCurrentUser = computed(() => {
  const uid = currentUserId.value
  if (!uid) return false
  // Consider local selection first (optimistic UI) so the "Listo" button appears
  if (selectedCharacterId.value) return true
  // Fallback: check server-provided selected_characters with a few common shapes
  const selected = room.value?.selected_characters || []
  return selected.some((sc: any) => {
    if (!sc) return false
    if (sc.user_id === uid) return true
    if ((sc as any).character_id && (sc as any).character_id === selectedCharacterId.value) return true
    if ((sc as any).character && (sc as any).character._id && (sc as any).character._id === selectedCharacterId.value) return true
    return false
  })
})

const canStartGame = computed(() => {
  if (!room.value || !isAdmin.value) return false
  const allReady = room.value.members?.length === room.value.ready_players?.length
  const allHaveCharacters = room.value.members?.length === room.value.selected_characters?.length
  return allReady && allHaveCharacters && room.value.game_state === 'waiting'
})

/* ---------- UI helpers ---------- */
function showCharacterDetails(character: Character) { detailedCharacter.value = character }
function closeCharacterDetails() { detailedCharacter.value = null }
function showTooltip(character: Character, e: MouseEvent) {
  tooltipCharacter.value = character
  tooltipX.value = e.clientX + 10
  tooltipY.value = e.clientY - 10
  showTooltipFlag.value = true
}
function hideTooltip() { showTooltipFlag.value = false; tooltipCharacter.value = null }
function showCharacterOptions(character: Character) { characterToSelect.value = character }
function closeCharacterModal() { characterToSelect.value = null }
function selectThisCharacter() { if (characterToSelect.value) { selectCharacter(characterToSelect.value._id); characterToSelect.value = null } }

/* ---------- WS ---------- */
function connectWebSocket(retry = 0) {
  const token = localStorage.getItem('access_token') || localStorage.getItem('token') || ''
  if (!token || !roomId || roomId === 'undefined') {
    if (retry < 3) setTimeout(() => connectWebSocket(retry + 1), 800)
    return
  }

  const base = import.meta.env.VITE_WS_BASE_URL ||
    ((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host)

  try { ws.value?.close() } catch {}
  ws.value = new WebSocket(`${base}/api/ws/room/${roomId}?token=${encodeURIComponent(token)}`)

  ws.value.onopen = () => { isConnected.value = true; console.log('[RoomWS] connected') }
  ws.value.onclose = (e) => {
    isConnected.value = false
    console.log('[RoomWS] disconnected', e.reason)
    if (shouldReconnect.value && e.code !== 1008) setTimeout(() => connectWebSocket(), 3000)
  }
  ws.value.onerror = (err) => {
    console.warn('[RoomWS] error (suppress reconnect)', err)
    // La room probablemente fue eliminada al iniciar el juego → no reconectar
    shouldReconnect.value = false
    try { ws.value?.close() } catch {}
  }
  ws.value.onmessage = (evt) => {
    try {
      const raw = JSON.parse(evt.data)
      const type = raw.type || raw.event
      const data = raw.data || raw.payload || {}
      handleWs(type, data)
    } catch (err) {
      console.error('[RoomWS] bad message', err, evt.data)
    }
  }
}

function handleWs(type: string, data: any) {
  switch (type) {
    case 'room_update': {
      if (room.value) room.value = { ...room.value, ...data }
      updateRoomStats()
      const s = data?.game_state || room.value?.game_state
      const g = data?.game_id   || (room.value as any)?.game_id
      if (s === 'playing' && g) router.replace(`/game/${g}`)
      break
    }
    
    // ✅ Redirección simultánea al iniciar juego
    case 'game_started': {
      const gameId = data?.game_id
      if (gameId) {
        console.log('[WS] Game started, redirecting to:', gameId)
        // Desconectar WS del room antes de redirigir
        if (ws.value) {
          shouldReconnect.value = false
          ws.value.close()
        }
        router.replace(`/game/${gameId}`)
      }
      break
    }
    
    case 'room_closed': {
      // Fallback si no llegó game_started, también salir del lobby
      const gameId = (room.value as any)?.game_id
      if (gameId) {
        console.log('[WS] Room closed, redirecting to game:', gameId)
        // Desconectar WS del room antes de redirigir
        if (ws.value) {
          shouldReconnect.value = false
          ws.value.close()
        }
        router.replace(`/game/${gameId}`)
      } else {
        router.replace({ name: 'rooms' })
      }
      break
    }
    
    case 'new_message': {
      if (!room.value) break
      room.value.messages = [...(room.value.messages || []), data]
      scrollToBottom()
      break
    }
    case 'ready_update': {
      if (!room.value) break
      room.value.ready_players = data.ready_players || room.value.ready_players
      readyCount.value = data.ready_count ?? readyCount.value
      totalMembers.value = data.total_members ?? totalMembers.value
      break
    }
    case 'character_selected': {
      if (!room.value) break
      const idx = room.value.selected_characters.findIndex((sc: any) => sc.user_id === data.user_id)
      if (idx >= 0) room.value.selected_characters[idx] = data
      else room.value.selected_characters.push(data)
      break
    }
    case 'chapter_update': {
      const gid = (room.value as any)?.game_id
      if (gid) router.replace(`/game/${gid}`)
      break
    }
    case 'game_state_change': {
      if (!room.value) break
      room.value.game_state = data.game_state
      const gid = data?.game_id || (room.value as any)?.game_id
      if (data.game_state === 'playing' && gid) {
        router.replace(`/game/${gid}`)
      }
      break
    }
    case 'room:started': {
      console.log('[WS] Room started event received:', data)
      isStartingGame.value = true
      const gameId = data?.game_id
      if (gameId) {
        // Pequeño delay para mostrar el estado de "iniciando"
        setTimeout(() => {
          if (ws.value) { shouldReconnect.value = false; try { ws.value.close() } catch {} }
          router.replace(`/game/${gameId}`)
        }, 1000)
      }
      break
    }
    default:
      // otros tipos ignorados
      break
  }
}

function sendWebSocketMessage(type: string, payload: any = {}) {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    // formato simple compatible con el backend actual
    ws.value.send(JSON.stringify({ type, ...payload }))
  }
}

/* ---------- Loaders ---------- */
function updateRoomStats() {
  if (!room.value) return
  readyCount.value = room.value.ready_players?.length || 0
  totalMembers.value = room.value.members?.length || 0
}

async function loadRoom() {
  if (!roomId || roomId === 'undefined') {
    router.push('/rooms')
    return
  }
  try {
    const { data } = await apiClient.get(`/rooms/${roomId}`)
    room.value = data
    // redirección inmediata si ya está en juego
    const state = (room.value as any)?.game_state
    const gid = (room.value as any)?.game_id
    if (state === 'playing' && gid) {
      router.replace(`/game/${gid}`)  // evita parpadeo al volver
      return
    }
    updateRoomStats()
  } catch (error: any) {
    console.error('Error loading room:', error?.response?.data || error)
    
    // ✅ Manejar sala cerrada (410 Gone) 
    if (error?.response?.status === 410) {
      const redirectGameId = error?.response?.data?.redirect_game_id
      if (redirectGameId) {
        router.replace({ name: 'game', params: { id: redirectGameId } })
      } else {
        router.replace({ name: 'rooms' })
      }
      return
    }
    
    if (error?.response?.status === 404) {
      // La sala no existe o fue eliminada, redirigir a mis partidas
      router.push('/my-games')
    }
  }
}

async function loadMyCharacters() {
  try {
    const { data } = await apiClient.get('/characters')
    myCharacters.value = data
  } catch (e) {
    console.error('Error loading characters:', e)
  }
}

async function loadCurrentUser() {
  try {
    // local first
    const saved = localStorage.getItem('user')
    if (saved) {
      const parsed = JSON.parse(saved)
      const localId = parsed?.id || parsed?._id
      if (localId) currentUserId.value = String(localId)
    }
    // refresh
    const { data } = await apiClient.get('/auth/me')
    const apiId = data?.id || data?._id
    if (apiId) {
      currentUserId.value = String(apiId)
      try {
        const u = JSON.parse(localStorage.getItem('user') || '{}')
        if (u && !u.id) { u.id = String(apiId); localStorage.setItem('user', JSON.stringify(u)) }
      } catch {}
    }
  } catch (e) { console.error('Error loading current user:', e) }
}

/* ---------- Actions ---------- */
async function selectCharacter(characterId: string) {
  try {
    await apiClient.post(`/rooms/${roomId}/select-character`, { character_id: characterId })
    selectedCharacterId.value = characterId
    // esperar actualización WS
  } catch (error: any) {
    console.error('Error selecting character:', error?.response?.data || error)
    alert(error?.response?.data?.detail || 'Error al seleccionar personaje')
  }
}

function toggleReady() { sendWebSocketMessage('toggle_ready') }

async function sendMessage() {
  if (!newMessage.value.trim()) return
  sendWebSocketMessage('chat_message', { message: newMessage.value, message_type: 'chat' })
  newMessage.value = ''
}

async function sendAction() {
  if (!newAction.value.trim()) return
  try {
    await apiClient.post(`/rooms/${roomId}/action`, { action: newAction.value, character_id: selectedCharacterId.value })
    newAction.value = ''
    await loadRoom()
  } catch (error: any) {
    alert(error?.response?.data?.detail || 'Error al enviar acción')
  }
}

function getUserName(userId: string): string {
  const m = room.value?.members?.find((x) => x.user_id === userId)
  return m?.username || 'Usuario desconocido'
}

function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  })
}

async function startGame() {
  if (!canStartGame.value) return
  isStartingGame.value = true
  
  try {
    // ✅ Timeout corto: solo queremos el gameId
    const resp = await apiClient.post(`/rooms/${roomId}/start-game`, {}, { timeout: 8000 })
    const gid = resp?.data?.game_id || (room.value as any)?.game_id
    if (gid) {
      // Navegar inmediatamente
      if (ws.value) { shouldReconnect.value = false; try { ws.value.close() } catch {} }
      router.replace(`/game/${gid}`)
      return
    }
    throw new Error('No game_id in response')
  } catch (error: any) {
    console.error('Error starting game (will try fallback):', error?.response?.data || error)
    
    // ✅ Fallback 1: El juego se está creando en background, escuchar WS
    if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
      console.log('[startGame] Request timeout, waiting for WebSocket confirmation...')
      // El WS ya maneja game_started y room:started
      return
    }
    
    // ✅ Fallback 2: Polling a /api/games/my
    console.log('[startGame] Trying polling fallback...')
    const startTime = Date.now()
    const poll = async () => {
      if (Date.now() - startTime > 25000) {
        throw new Error('Game start timeout after 25s')
      }
      try {
        const { data: games } = await apiClient.get('/games/my')
        const latestGame = games?.find((g: any) => 
          g.room_id === roomId && 
          new Date(g.created_at).getTime() > startTime - 5000
        )
        if (latestGame?.id || latestGame?._id) {
          const gameId = latestGame.id || latestGame._id
          if (ws.value) { shouldReconnect.value = false; try { ws.value.close() } catch {} }
          router.replace(`/game/${gameId}`)
          return
        }
      } catch (pollError) {
        console.error('Polling error:', pollError)
      }
      // Reintentar en 2s
      setTimeout(poll, 2000)
    }
    
    poll().catch((pollError) => {
      console.error('Polling failed:', pollError)
      alert('No se pudo iniciar el juego después de varios intentos. Por favor, intenta de nuevo.')
      isStartingGame.value = false
    })
  }
}

async function updateRoomSettings() {
  if (!room.value || !isAdmin.value) return
  try {
    await apiClient.patch(`/rooms/${roomId}`, {
      discussion_time: room.value.discussion_time,
      auto_continue: room.value.auto_continue,
      continue_time: room.value.continue_time,
      max_chapters: room.value.max_chapters
    })
  } catch (error: any) {
    console.error('Error updating room settings:', error?.response?.data || error)
    alert(error?.response?.data?.detail || 'Error al actualizar configuración')
  }
}

async function leaveRoom() {
  const confirmed = confirm('¿Estás seguro de que quieres salir de esta sala?')
  if (!confirmed) return
  try {
    await apiClient.post(`/rooms/${roomId}/leave`)
    alert('Has salido de la sala exitosamente.')
    router.push('/rooms')
  } catch (error: any) {
    console.error('Error leaving room:', error?.response?.data || error)
    alert(error?.response?.data?.detail || 'Error al salir de la sala')
  }
}

/* ---------- Lifecycle ---------- */
onMounted(async () => {
  if (!isValidObjectId(roomId)) {
    // nada de alert(); simplemente volvemos al listado
    router.replace({ name: 'rooms' })
    return
  }
  // Conectar WS primero (para no perder room:started)
  connectWebSocket()
  // Cargar datos en paralelo
  Promise.all([loadCurrentUser(), loadRoom(), loadMyCharacters()]).catch(() => {})
})

onBeforeUnmount(() => {
  shouldReconnect.value = false
  try { ws.value?.close() } catch {}
})
</script>
