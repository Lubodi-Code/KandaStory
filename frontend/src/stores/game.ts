import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ApiGame } from '../api'

export interface Game {
  _id: string
  name: string
  room_id: string
  world_id?: string
  max_chapters: number
  max_players: number
  current_chapter: number
  game_state: 'playing' | 'action_phase' | 'finished'
  settings: {
    allow_suggestions: boolean
    discussion_time: number
    auto_continue: boolean
    continue_time: number
  }
  created_at: string
  updated_at?: string
}

export interface GameChapter {
  _id: string
  game_id: string
  chapter_number: number
  content: string
  created_at: string
}

export interface GameMessage {
  _id: string
  game_id: string
  user_id: string
  message: string
  message_type: string
  timestamp: string
}

export interface GameAction {
  _id: string
  game_id: string
  user_id: string
  character_id?: string
  action: string
  status: 'pending' | 'approved' | 'rejected'
  chapter_number: number
  created_at: string
}

export const useGameStore = defineStore('game', () => {
  const game = ref<Game | null>(null)
  const chapters = ref<GameChapter[]>([])
  const messages = ref<GameMessage[]>([])
  const actions = ref<GameAction[]>([])
  const remainingSeconds = ref<number>(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed properties
  const currentChapter = computed(() => game.value?.current_chapter ?? 0)
  const gameState = computed(() => game.value?.game_state ?? 'playing')
  const isFinished = computed(() => gameState.value === 'finished')
  const isActionPhase = computed(() => gameState.value === 'action_phase')

  // Actions
  async function fetchGame(gameId: string) {
    try {
      loading.value = true
      error.value = null
      const data = await ApiGame.getGame(gameId)
      game.value = data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error al cargar el juego'
      console.error('Error fetching game:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchChapters(gameId: string) {
    try {
      const data = await ApiGame.getChapters(gameId)
      chapters.value = Array.isArray(data) ? data : data?.items ?? []
    } catch (err: any) {
      console.error('Error fetching chapters:', err)
    }
  }

  async function fetchMessages(gameId: string, limit = 50, offset = 0) {
    try {
      const data = await ApiGame.getMessages(gameId, limit, offset)
      messages.value = Array.isArray(data) ? data : data?.items ?? []
    } catch (err: any) {
      console.error('Error fetching messages:', err)
    }
  }

  async function fetchActions(gameId: string, status?: string) {
    try {
      const data = await ApiGame.getActions(gameId, status)
      actions.value = Array.isArray(data) ? data : data?.items ?? []
    } catch (err: any) {
      console.error('Error fetching actions:', err)
    }
  }

  async function markReady(gameId: string, ready = true) {
    try {
      await ApiGame.markContinue(gameId, { ready })
    } catch (err: any) {
      console.error('Error marking ready:', err)
      throw err
    }
  }

  async function proposeAction(gameId: string, action: string, characterId?: string) {
    try {
      const newAction = await ApiGame.proposeAction(gameId, {
        action,
        character_id: characterId,
        chapter_number: currentChapter.value
      })
      
      // Actualizar la lista de acciones localmente
      actions.value.push(newAction)
      return newAction
    } catch (err: any) {
      console.error('Error proposing action:', err)
      throw err
    }
  }

  async function sendMessage(gameId: string, message: string, messageType = 'chat') {
    try {
      const newMessage = await ApiGame.postMessage(gameId, {
        message,
        message_type: messageType
      })
      
      // Actualizar la lista de mensajes localmente
      messages.value.push(newMessage)
      return newMessage
    } catch (err: any) {
      console.error('Error sending message:', err)
      throw err
    }
  }

  async function updateGameSettings(gameId: string, settings: {
    discussion_time?: number
    auto_continue?: boolean
    continue_time?: number
    require_all_players?: boolean
    allow_suggestions?: boolean
    max_chapters?: number
  }) {
    try {
      await ApiGame.updateSettings(gameId, settings)
      // Refrescar el juego para obtener los settings actualizados
      await fetchGame(gameId)
    } catch (err: any) {
      console.error('Error updating settings:', err)
      throw err
    }
  }

  // WebSocket event handlers
  function onChapterCreated(payload: { chapter_number: number; discussion_seconds?: number }) {
    console.log('[GameStore] Chapter created:', payload)
    
    // Actualizar el juego y capítulos
    if (game.value) {
      fetchGame(game.value._id)
      fetchChapters(game.value._id)
    }
    
    // Establecer el tiempo de discusión si se proporciona
    if (payload.discussion_seconds) {
      remainingSeconds.value = payload.discussion_seconds
    }
  }

  function onActionPhaseStarted(payload: { ends_at: string; seconds_total: number; remaining_seconds?: number }) {
    console.log('[GameStore] Action phase started:', payload)
    remainingSeconds.value = payload.remaining_seconds ?? payload.seconds_total
    
    // Actualizar el estado del juego
    if (game.value) {
      game.value.game_state = 'action_phase'
    }
  }

  function onContinueUpdate(payload: { ready_count: number; total: number; remaining_seconds: number }) {
    console.log('[GameStore] Continue update:', payload)
    remainingSeconds.value = payload.remaining_seconds
  }

  function onActionsUpdated(payload: { chapter_number: number }) {
    console.log('[GameStore] Actions updated:', payload)
    
    // Refrescar las acciones para el capítulo actual
    if (game.value) {
      fetchActions(game.value._id)
    }
  }

  // Timer management
  let timerInterval: number | null = null

  function startTimer(seconds: number) {
    stopTimer()
    remainingSeconds.value = seconds
    
    timerInterval = window.setInterval(() => {
      if (remainingSeconds.value > 0) {
        remainingSeconds.value--
      } else {
        stopTimer()
      }
    }, 1000)
  }

  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
  }

  // Reset store
  function resetGame() {
    game.value = null
    chapters.value = []
    messages.value = []
    actions.value = []
    remainingSeconds.value = 0
    error.value = null
    stopTimer()
  }

  return {
    // State
    game,
    chapters,
    messages,
    actions,
    remainingSeconds,
    loading,
    error,
    
    // Computed
    currentChapter,
    gameState,
    isFinished,
    isActionPhase,
    
    // Actions
    fetchGame,
    fetchChapters,
    fetchMessages,
    fetchActions,
    markReady,
    proposeAction,
    sendMessage,
    updateGameSettings,
    
    // WebSocket handlers
    onChapterCreated,
    onActionPhaseStarted,
    onContinueUpdate,
    onActionsUpdated,
    
    // Timer
    startTimer,
    stopTimer,
    
    // Utils
    resetGame
  }
})
