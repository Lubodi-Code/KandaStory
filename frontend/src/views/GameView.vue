<template>
  <div v-if="room" class="max-w-7xl mx-auto p-4">
  <!-- Header del juego -->
  <div class="card-navy rounded-lg shadow-md p-6 mb-6 card-accent">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-3xl md:text-4xl font-bold text-gold-300">{{ room.name }}</h1>
          <p class="text-emerald-200">Mundo: {{ room.world?.title || 'Mundo desconocido' }}</p>
          <p class="text-sm text-emerald-600 dark:text-emerald-400">
            Capítulo {{ Math.max(room.current_chapter, room.chapters.length) }} de {{ room.max_chapters }} •
            Estado: {{ getGameStateText(room.game_state) }}
          </p>
        </div>
        <div class="flex space-x-2">
          <button @click="showExitModal = true" class="btn-gold btn-outline">
            Salir
          </button>
        </div>
      </div>
    </div>

    <!-- Componente de lectura mejorado -->
    <StoryReader
      v-if="room.game_state === 'playing' || room.game_state === 'finished' || room.game_state === 'action_phase'"
      :game-id="gameId"
      :chapters="formattedChapters"
      :current-chapter="Math.max(room.current_chapter || 0, (room.chapters || []).length)"
      :finished="room.game_state === 'finished'"
      :allow-actions="room.allow_actions || false"
      :show-timer="isActionPhase"
      :remaining-seconds="continueStatus.remaining_seconds || 0"
      :ready-count="continueStatus.ready_count || 0"
      :total-players="continueStatus.total || 0"
      :ready="false"
      :button-disabled="buttonDisabled"
      :submitted-action="submittedInThisPhase"
      @submit:action="handleSubmitAction"
      @click:ready="handleMarkReady"
      @download="downloadSeries"
    />

    <!-- Estado de espera -->
  <div v-else class="card-navy rounded-lg shadow-md p-6 text-center card-accent">
  <div class="text-emerald-200">
        <div class="text-4xl mb-4">⏳</div>
        <p class="text-lg">Preparando la partida...</p>
      </div>
    </div>

    <!-- Acciones pendientes: ya no se muestran (acciones son privadas). -->

    <!-- Chat general -->
  <div class="grid grid-cols-1 lg:grid-cols-1 gap-6">
      <!-- Chat general -->
  <div class="bg-black rounded-lg shadow-md p-6">
  <h2 class="text-xl font-bold mb-4 text-gold-300">Chat general</h2>
    <div ref="chatContainer" class="border rounded p-4 h-64 overflow-y-auto mb-4 space-y-2 border-emerald-800">
          <div v-for="message in chatMessages" :key="message.id || message.timestamp" 
               :class="getMessageClasses(message.message_type)"
               class="p-2 rounded">
            <div class="flex justify-between items-start">
              <div>
                <span class="font-semibold">{{ message.username }}</span>
                <p>{{ message.message }}</p>
              </div>
              <span class="text-xs text-gray-500">{{ formatTime(message.timestamp) }}</span>
            </div>
          </div>
        </div>
        <div class="flex space-x-2">
          <input
            v-model="newMessage"
            @keyup.enter="sendMessage"
            placeholder="Escribe un mensaje..."
            class="flex-1 border border-emerald-800 rounded px-3 py-2 bg-navy-900/40 text-white placeholder:text-zinc-400 outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <button 
            @click="sendMessage"
            :disabled="!newMessage.trim()"
            :class="['btn-gold', { 'opacity-50 cursor-not-allowed': !newMessage.trim() }]"
          >
            Enviar
          </button>
        </div>
      </div>
    </div>

    <!-- Modal de confirmación de salida -->
    <div v-if="showExitModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-bold mb-4">Confirmar Salida</h3>
        <p class="text-gray-600 mb-6">
          ¿Estás seguro de que quieres salir del juego? Esto te llevará de vuelta al menú principal.
        </p>
        <div class="flex justify-end space-x-2">
          <button @click="showExitModal = false" 
                  class="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50">
            Cancelar
          </button>
          <button @click="exitGame" 
                  class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
            Salir
          </button>
        </div>
      </div>
    </div>

    <!-- Loader sutil durante avance al siguiente capítulo -->
    <div v-if="isAdvancing" class="fixed bottom-4 right-4 z-40">
      <div class="inline-flex items-center gap-2 bg-black/70 text-amber-200 px-3 py-2 rounded-md border border-amber-500/30">
        <span class="w-4 h-4 border-2 rounded-full border-current border-r-transparent animate-spin"></span>
        Generando capítulo…
      </div>
    </div>
  </div>
  
  <div v-else class="flex justify-center items-center min-h-screen">
    <p class="text-lg text-gray-600">Cargando juego...</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StoryReader from '../components/StoryReader.vue'
import { useAuthStore } from '../stores/auth'
import apiGames, { type GameMessageDoc, type GameActionDoc } from '../api/ApiGames'
import { apiClient } from '../lib/api'

const route = useRoute()
const router = useRouter()

const isValidObjectId = (s: string) => /^[0-9a-fA-F]{24}$/.test(s)
let gameId = ref(String(route.params.id))
const roomIdForGame = ref<string | null>(null)

// ---------- state ----------
const room = ref<any | null>(null)
const loading = ref(true)
const error = ref('')
const newMessage = ref('')
const newAction = ref('')
const continueStatus = ref<{ ready_count?: number; total?: number; remaining_seconds?: number }>({})
const showExitModal = ref(false)
const submittedInThisPhase = ref(false)
const loadingChapter = ref(false)
const isTyping = ref(false)
const showAllChapters = ref(false)
const displayedChapters = ref<string[]>([])
const generatingNext = ref(false) // legacy; kept to avoid breaking, but not used for overlay
const isAdvancing = ref(false)

// Controles para evitar doble POST
const sentAutoContinue = ref(false)
const buttonDisabled = ref(false)

// Computed properties para StoryReader
const formattedChapters = computed(() => {
  return room.value?.chapters?.map((ch: any) => ch.content || ch) || []
})

// Event handlers para StoryReader
const handleSubmitAction = async (action: string) => {
  newAction.value = action
  await submitAction()
}

const handleMarkReady = async () => {
  await markContinue(true)
}

const isActionPhase = computed(() => room.value?.game_state === 'action_phase')

let ws: WebSocket | null = null
const isRoomConnected = ref(false)
const isConnected = ref(false)
const chatContainer = ref<HTMLElement>()
const auth = useAuthStore()
const chatMessages = computed(() => {
  const msgs = room.value?.messages || []
  return (msgs as any[]).filter((m: any) => m.message_type === 'chat' || m.message_type === 'system')
})

// ---------- helpers ----------
function getUserName(userId: string): string {
  const m = room.value?.members?.find((x: any) => x.user_id === userId)
  return m?.username || 'Usuario desconocido'
}

function getGameStateText(state: string): string {
  const states: Record<string, string> = {
    waiting: 'Esperando jugadores',
    character_selection: 'Selección de personajes',
    playing: 'Jugando',
    action_phase: 'Fase de acciones',
    finished: 'Finalizado'
  }
  return states[state] || state
}

function getMessageClasses(t: string, msg?: any): string {
  // Base styles: dark background, rounded, and padding handled in template
  const base = 'p-2 rounded';
  if (t === 'system') return base + ' bg-emerald-900/40 border-l-4 border-emerald-500 text-emerald-200'
  if (t === 'story') return base + ' bg-emerald-900/30 border-l-4 border-emerald-500 text-emerald-100'
  if (t === 'action') return base + ' bg-amber-900/30 border-l-4 border-amber-500 text-amber-100'

  // chat messages: if it's the current user's message, highlight in emerald
  if (t === 'chat') {
    const me = auth.user?.id || null
    const isMine = msg && (msg.user_id === me || msg.username === auth.user?.username)
    // Ensure chat text is white for readability against dark backgrounds
    return base + (isMine ? ' bg-emerald-900/60 text-white self-end' : ' bg-neutral-800/60 text-white')
  }

  return base + ' bg-neutral-800/60 text-zinc-200'
}
function formatTime(ts: string): string {
  return new Date(ts).toLocaleTimeString()
}

// ---------- countdown local ----------
let actionTimer: number | null = null
function clearActionTimer() {
  if (actionTimer) { clearInterval(actionTimer); actionTimer = null }
}
function startActionCountdown(seconds: number | undefined) {
  const s = Math.max(0, Number(seconds ?? 0))
  continueStatus.value = { ...continueStatus.value, remaining_seconds: s }
  clearActionTimer()
  sentAutoContinue.value = false // Reset al iniciar nuevo countdown
  if (s === 0) return
  actionTimer = window.setInterval(() => {
    const cur = Math.max(0, (continueStatus.value.remaining_seconds ?? 0) - 1)
    continueStatus.value = { ...continueStatus.value, remaining_seconds: cur }
    if (cur <= 0) clearActionTimer()
  }, 1000)
}

// ---------- timer watcher ----------
watch(() => continueStatus.value.remaining_seconds, (newSeconds) => {
  if (newSeconds === 0 && !sentAutoContinue.value && isActionPhase.value) {
    sentAutoContinue.value = true
    buttonDisabled.value = true
    console.log('[timer] reached 0, sending auto continue')
    markContinue(true).catch(console.error)
  }
})

// ---------- API ----------
async function loadGameRoom() {
  try {
    loading.value = true

    // Permitir que /game/:id venga con un roomId y resolverlo
    if (!isValidObjectId(gameId.value)) {
      try {
        const roomResp = await apiClient.get(`/rooms/${gameId.value}`)
        const gid = roomResp?.data?.game_id
        if (gid && isValidObjectId(gid)) {
          router.replace({ name: 'game', params: { id: gid } })
          return
        }
      } catch {
        router.replace({ name: 'rooms' })
        return
      }
    }

  const meta = await apiGames.get(gameId.value)
  roomIdForGame.value = meta.room_id || null
    const chapters = await apiGames.listChapters(gameId.value)
    const messages = await apiGames.listMessages(gameId.value, 50, 0)
    const members = await apiGames.members(gameId.value) // ✅ Cargar miembros

    // Crear mapa de usuarios para obtener nombres
    const userById = new Map(members.map((m: any) => [m.user_id, m.username]))

    room.value = {
      id: meta._id,
      name: meta.name,
      world: { title: '' },
      max_chapters: meta.max_chapters,
      current_chapter: meta.current_chapter || 0,
      chapters: chapters.map((c: any) => c.content),
      messages: messages.map((m: any) => ({
        user_id: m.user_id,
        username: userById.get(m.user_id) || '', // ✅ Mapear nombre correctamente
        message: m.content,
        timestamp: m.timestamp,
        message_type: m.type
      })),
      members: members, // ✅ Agregar miembros al room
      game_state: meta.game_state,
      allow_actions: meta.settings?.allow_suggestions ?? true,
    }

    // Si ya entramos en mitad de una fase de acciones, iníciala en la UI
    if ((meta.settings?.allow_suggestions ?? true)) {
      // si el servidor ya está en action_phase, arrancamos con su tiempo
      if (meta.game_state === 'action_phase') {
        const endsAt = (meta as any)?.phase?.ends_at
        const secs = endsAt
          ? Math.max(0, Math.floor((new Date(endsAt).getTime() - Date.now()) / 1000))
          : (meta.settings?.discussion_time ?? 300)
        startActionCountdown(secs)
      } else {
        // fallback: si acabas de ver el capítulo y no llegó el evento, abre fase de acciones
        // (esto es seguro: luego el WS 'continue_update' re-sincroniza tiempos)
        if ((room.value?.chapters?.length ?? 0) > 0 && room.value?.game_state === 'playing') {
          room.value.game_state = 'action_phase'
          startActionCountdown(meta.settings?.discussion_time ?? 300)
          submittedInThisPhase.value = false
        }
      }
    }

    // Ya no conectamos al canal de sala desde GameView; solo canal de juego

    try { if (room.value?.id) localStorage.setItem('current_game_id', room.value.id) } catch {}
  } catch (err: any) {
    console.error('Error loading game room:', err)
    try { localStorage.removeItem('current_game_id') } catch {}
    error.value = err?.response?.data?.detail
      || (err?.response?.status === 404 ? 'Partida no encontrada (404)' : 'Error al cargar la partida')
  } finally {
    loading.value = false
  }
}

async function sendMessage() {
  if (!newMessage.value.trim()) return
  const text = newMessage.value.trim()
  newMessage.value = ''

  // 1) Optimista en UI
  if (room.value) {
    const mine = {
      user_id: auth.user?.id || '',
      username: auth.user?.username || '',
      message: text,
      timestamp: new Date().toISOString(),
      message_type: 'chat'
    }
    room.value.messages = [...(room.value.messages || []), mine]
    nextTick(() => {
      chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
    })
  }

  try {
    // 2) Enviar por WebSocket de sala (canal de chat actual)
    if (ws && isRoomConnected.value) {
      ws.send(JSON.stringify({
        type: 'chat_message',
        message: text,
        message_type: 'chat'
      }))
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error al enviar mensaje'
    console.error('Error sending message:', err)
    // (opcional) revertir o marcar error en el último mensaje
  }
}

async function submitAction() {
  if (!newAction.value.trim()) return
  try {
    const payload = { action: newAction.value.trim() } as unknown as Omit<GameActionDoc,'game_id'|'user_id'|'created_at'|'_id'|'status'>
    await apiGames.proposeAction(gameId.value, payload)
    newAction.value = ''
    submittedInThisPhase.value = true
    // Ya no necesitamos markContinue(true) aquí - el backend lo hace automáticamente
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error al enviar acción'
    console.error('Error submitting action:', err)
  }
}

async function exitGame() {
  try {
    await apiClient.post(`/games/${gameId.value}/leave`)
    try { localStorage.removeItem('current_game_id') } catch {}
    router.push('/my-games')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error al salir del juego'
    console.error('Error leaving game:', err)
  }
  showExitModal.value = false
}

async function markContinue(ready: boolean) {
  if (buttonDisabled.value) return // Evitar doble envío
  
  console.log('[continue] sending', { gameId: gameId.value, ready })
  buttonDisabled.value = true
  isAdvancing.value = true
  
  try {
    await apiClient.post(`/games/${gameId.value}/continue`, { ready })
    // la UI se actualizará con game:continue_update; si no llega, mantenemos el timer local
  } catch (e: any) {
    console.error('Error marking continue:', e)
    if (!e.code || e.code !== 'ECONNABORTED') {
      alert(e?.response?.data?.detail || 'No se pudo marcar listo.')
    }
  } finally {
    // Re-habilitar después de 2 segundos para permitir cambios de estado
    setTimeout(() => {
      buttonDisabled.value = false
    }, 2000)
  }
}

async function ensureNextChapter() {
  // Polling reducido ya que ahora tenemos WebSocket confiable
  const start = Date.now()
  const maxMs = 10000 // 10s (reducido de 15s)
  generatingNext.value = true
  try {
    let lastCount = room.value?.chapters?.length ?? 0
    let attempts = 0
    const maxAttempts = 3 // máximo 3 intentos
    
    while (Date.now() - start < maxMs && attempts < maxAttempts) {
      // si el WS ya lo trajo, salimos
      const cur = room.value?.chapters?.length ?? 0
      if (cur > lastCount) break

      // revalida desde API (menos frecuente)
      const chapters = await apiGames.listChapters(gameId.value)
      if (chapters.length > lastCount) {
        room.value!.chapters = chapters.map((c: any) => c.content)
        room.value!.current_chapter = chapters.length
        console.log('[ensureNextChapter] Chapter found via polling')
        break
      }
      
      attempts++
      await new Promise(r => setTimeout(r, 3000)) // 3s entre intentos (era 1.2s)
    }
    
    if (attempts >= maxAttempts) {
      console.log('[ensureNextChapter] Max attempts reached, relying on WebSocket')
    }
  } finally {
    generatingNext.value = false
  }
}

// (scrollToChapter removed; StoryReader handles scrolling)

// ---------- WebSocket ----------
function connectWebSocket() {
  const raw = localStorage.getItem('access_token') || localStorage.getItem('token')
  if (!raw) return
  const token = encodeURIComponent(raw)
  const base = import.meta.env.VITE_WS_BASE_URL || ((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host)
  ws = new WebSocket(`${base}/api/ws/game/${gameId.value}?token=${token}`)

  ws.onopen = () => { isConnected.value = true; console.log('[GameWS] connected') }

  ws.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data)
      switch (data.type) {
        case 'game:chapter_created': {
          const chapterNumber = data.data?.chapter_number
          const chapters = await apiGames.listChapters(gameId.value)
          const ch = chapters.find((c: any) => c.chapter_number === chapterNumber)
          if (ch && room.value) {
            loadingChapter.value = true
            await typeChapter(ch.content, chapterNumber)
          }
          
          // Reset de controles al recibir nuevo capítulo
          sentAutoContinue.value = false
          buttonDisabled.value = false
          submittedInThisPhase.value = false
          isAdvancing.value = false
          
          // --- Fallback: entrar a fase de acciones después de crear capítulo ---
          if (room.value) room.value.game_state = 'action_phase'
          
          // intenta usar segundos del evento; si no, del meta; si no, 300
          let secs = Number(data?.data?.discussion_seconds ?? 0)
          if (!secs) {
            try {
              const meta = await apiGames.get(gameId.value)
              secs = Number((meta as any)?.phase?.ends_at
                ? Math.max(0, Math.floor((new Date((meta as any).phase.ends_at).getTime() - Date.now())/1000))
                : (meta.settings?.discussion_time ?? 300))
            } catch { secs = 300 }
          }
          startActionCountdown(secs)
          continueStatus.value = {
            ready_count: 0,
            total: continueStatus.value?.total
          }
          break
        }

        case 'game:action_phase_started': {
          console.log('[WS] Action phase started - resetting state')
          if (room.value) room.value.game_state = 'action_phase'
          
          // ✅ Reset completo del estado de "listo"
          sentAutoContinue.value = false
          buttonDisabled.value = false
          submittedInThisPhase.value = false
          
          // ✅ Reset del contador de listos
          const secs = data?.data?.remaining_seconds ?? data?.data?.seconds_total ?? 0
          continueStatus.value = {
            ready_count: 0,
            total: data?.data?.total ?? continueStatus.value?.total ?? 1,
            remaining_seconds: secs
          }
          
          startActionCountdown(secs || 300)
          console.log('[WS] State reset complete: ready=0, timer started')
          break
        }

        case 'game:continue_update': {
          console.log('[WS] Continue update:', data.data)
          continueStatus.value = {
            ready_count: data.data?.ready_count ?? continueStatus.value?.ready_count,
            total: data.data?.total ?? continueStatus.value?.total,
            remaining_seconds: data.data?.remaining_seconds ?? continueStatus.value?.remaining_seconds
          }
          
          // Re-sincronizar timer solo si viene el dato
          if (typeof data.data?.remaining_seconds === 'number') {
            startActionCountdown(data.data.remaining_seconds)
          }
          break
        }

        case 'game:state_changed': {
          // por si el backend emite un nombre diferente
          if (room.value) room.value.game_state = data?.data?.game_state || room.value.game_state
          if (room.value?.game_state !== 'action_phase') clearActionTimer()
          break
        }

        case 'game:new_message': {
          if (!room.value) break
          const m = data.data || {}
          // Normaliza campos al formato que usas en la UI
          const entry = {
            user_id: m.user_id,
            username: m.username || getUserName?.(m.user_id) || '', // fallback
            message: m.content || m.message,
            timestamp: m.timestamp,
            message_type: m.type || 'chat'
          }
          room.value.messages = [...(room.value.messages || []), entry]
          nextTick(() => {
            chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
          })
          break
        }

        case 'game:finished': {
          // Marcar juego como terminado
          if (room.value) {
            room.value.game_state = 'finished'
          }
          clearActionTimer()
          console.log('[GameWS] Juego terminado')
          break
        }

        default:
          break
      }
    } catch (err) {
      console.error('Error parsing WebSocket message:', err)
    }
  }

  ws.onclose = (ev) => {
    isConnected.value = false
    clearActionTimer()
    if ((ev?.reason || '').includes('Not a member')) {
      console.error('[GameWS] 403/1008: user not in game_members')
    }
    console.log('[GameWS] disconnected', ev?.reason || '')
  }

  ws.onerror = (error) => console.error('[GameWS] error:', error)
}

// ---------- typing effect ----------
async function typeChapter(text: string, chapterNumber: number) {
  try {
    isTyping.value = true
    loadingChapter.value = true
    const buffer: string[] = [...room.value!.chapters]
    buffer[chapterNumber - 1] = ''
    room.value!.chapters = buffer
    let shown = ''
    const chars = [...text]
    for (let i = 0; i < chars.length; i++) {
      shown += chars[i]
      room.value!.chapters[chapterNumber - 1] = shown
      await new Promise(r => setTimeout(r, i % 3 === 0 ? 5 : 0))
    }
    room.value!.current_chapter = chapterNumber
  } finally {
    isTyping.value = false
    loadingChapter.value = false
    updateDisplayedChapters()
  }
}
function updateDisplayedChapters() {
  if (!room.value) { displayedChapters.value = []; return }
  displayedChapters.value = showAllChapters.value ? room.value.chapters : room.value.chapters.slice(-1)
}
function downloadSeries(kind: 'txt'|'pdf') {
  if (!room.value) return
  
  // Usar la API del backend para exportar
  const url = `/api/games/${gameId.value}/export/${kind}`
  const link = document.createElement('a')
  const title = (room.value.name || 'KandaStory').replace(/[^a-z0-9\-]+/gi, '_')
  
  // Usar apiClient para incluir el token de autorización
  apiClient.get(url, {
    responseType: 'blob',
    headers: {
      'Accept': kind === 'pdf' ? 'application/pdf' : 'text/plain'
    }
  }).then(response => {
    const blob = new Blob([response.data], { 
      type: kind === 'pdf' ? 'application/pdf' : 'text/plain;charset=utf-8' 
    })
    link.href = URL.createObjectURL(blob)
    link.download = `${title}.${kind}`
    link.click()
    URL.revokeObjectURL(link.href)
  }).catch(error => {
    console.error('Error downloading file:', error)
    // Fallback al método anterior si la API no está disponible
    const content = room.value.chapters.map((c: string, i: number) => `Capítulo ${i + 1}\n\n${c}`).join("\n\n---\n\n")
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    link.href = URL.createObjectURL(blob)
    link.download = `${title}.txt`
    link.click()
    URL.revokeObjectURL(link.href)
  })
}

// ---------- lifecycle ----------
onMounted(async () => {
  connectWebSocket()                // 1) primero WS
  await loadGameRoom()              // 2) luego fetch
  if (!error.value) updateDisplayedChapters()
})
watch([showAllChapters, () => room.value?.chapters?.length], () => updateDisplayedChapters())
watch(() => route.params.id, async (nid) => {
  if (!nid) return
  gameId.value = String(nid)
  try { if (ws) ws.close() } catch {}
  clearActionTimer()
  connectWebSocket()                // primero WS
  await loadGameRoom()              // luego fetch
})
// Watcher para cuando el timer llegue a 0 - evitar doble POST
let sentAuto = false
watch(() => continueStatus.value.remaining_seconds, async (s) => {
  if (typeof s === 'number' && s <= 0 && room.value?.game_state === 'action_phase') {
    if (!sentAuto) {
      sentAuto = true
      console.log('[timer] reached 0, disabling UI and waiting for WS chapter_created event')
      // No hacer POST aquí - dejar que el backend maneje el timer
      // Solo deshabilitar UI y esperar el evento WebSocket
      await ensureNextChapter()
    }
  } else if (s && s > 0) {
    // Reset flag cuando el timer se reinicia
    sentAuto = false
  }
})
onBeforeUnmount(() => {
  clearActionTimer()
  if (ws) ws.close()
})
</script>
