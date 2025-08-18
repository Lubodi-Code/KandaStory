import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '../lib/api'

export interface Room {
  _id: string
  name: string
  world_id: string
  world?: any
  max_chapters: number
  max_players: number
  allow_suggestions: boolean
  discussion_time_minutes: number
  auto_continue: boolean
  continue_time: number
  require_all_players: boolean
  creator_id: string
  // Legacy field (older frontend)
  players?: string[]
  // Newer backend fields
  member_ids?: string[]
  current_members?: number
  game_state?: 'waiting' | 'active' | 'completed'
  is_user_member?: boolean
  status?: 'waiting' | 'active' | 'completed'
  created_at: string
  current_chapter?: number
}

export const useRoomsStore = defineStore('rooms', () => {
  const rooms = ref<Room[]>([])
  const userRoom = ref<Room | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const availableRooms = computed(() => 
    rooms.value.filter(room => room.status === 'waiting')
  )

  const activeRooms = computed(() => 
    rooms.value.filter(room => room.status === 'active')
  )

  // Actions
  async function loadRooms() {
    loading.value = true
    error.value = null
    try {
      // Verificar si el usuario está autenticado
      const token = localStorage.getItem('token')
      const endpoint = token ? '/rooms' : '/rooms/public'
      
      const response = await apiClient.get(endpoint)
      rooms.value = response.data
    } catch (err: any) {
      // Fallback a /rooms/public si la privada falla
      try {
        const { data } = await apiClient.get('/rooms/public')
        rooms.value = data
        error.value = null  // no mostrar bloque rojo
      } catch (err2: any) {
        error.value = err2.response?.data?.detail || 'No se pudieron cargar las salas'
        console.error('Error loading rooms:', err2)
      }
    } finally {
      loading.value = false
    }
  }

  async function loadUserRoom() {
    try {
      // Solo cargar la sala del usuario si está autenticado
      const token = localStorage.getItem('token')
      if (!token) {
        userRoom.value = null
        return
      }
      
      const response = await apiClient.get('/rooms/my-room')
      // Backend puede devolver { room, message } o el objeto de sala directamente
      const data = response.data
      const maybeRoom = (data && Object.prototype.hasOwnProperty.call(data, 'room')) ? data.room : data
      // Asignar solo si existe un _id válido; de lo contrario, considerar que NO hay sala
      userRoom.value = (maybeRoom && typeof maybeRoom === 'object' && '_id' in maybeRoom && (maybeRoom as any)._id)
        ? (maybeRoom as Room)
        : null
    } catch (e) {
      // No propagar este error a la UI principal
      console.warn('loadUserRoom failed (ignorado):', e)
      userRoom.value = null
    }
  }

  async function createRoom(roomData: Partial<Room>) {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.post('/rooms', roomData)
      const newRoom = response.data
      rooms.value.push(newRoom)
      userRoom.value = newRoom
      return newRoom
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error creating room'
      console.error('Error creating room:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function joinRoom(roomId: string) {
    loading.value = true
    error.value = null
    try {
      // Join returns ack; fetch full room after
      await apiClient.post(`/rooms/${roomId}/join`)
      const roomRes = await apiClient.get(`/rooms/${roomId}`)
      const updatedRoom: Room = roomRes.data

      // Update room in list if present
      const index = rooms.value.findIndex(r => r._id === roomId)
      if (index !== -1) {
        rooms.value[index] = updatedRoom
      }

      userRoom.value = updatedRoom
      return updatedRoom
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error joining room'
      console.error('Error joining room:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function leaveRoom(roomId: string) {
    loading.value = true
    error.value = null
    try {
  await apiClient.post(`/rooms/${roomId}/leave`)
  // Reload list to reflect updated counts and possible deletion
  await loadRooms()
      userRoom.value = null
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error leaving room'
      console.error('Error leaving room:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getRoomById(roomId: string) {
    try {
      const response = await apiClient.get(`/rooms/${roomId}`)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error getting room'
      console.error('Error getting room:', err)
      throw err
    }
  }

  async function deleteRoom(roomId: string) {
    loading.value = true
    error.value = null
    try {
      await apiClient.delete(`/rooms/${roomId}`)
      
      // Remove from list
      rooms.value = rooms.value.filter(r => r._id !== roomId)
      
      if (userRoom.value?._id === roomId) {
        userRoom.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error deleting room'
      console.error('Error deleting room:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    rooms,
    userRoom,
    loading,
    error,
    
    // Computed
    availableRooms,
    activeRooms,
    
    // Actions
    loadRooms,
    loadUserRoom,
    createRoom,
    joinRoom,
    leaveRoom,
    getRoomById,
    deleteRoom,
    clearError
  }
})
