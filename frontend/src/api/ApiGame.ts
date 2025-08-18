import { apiClient } from '../lib/api'

export interface Room {
  _id: string
  name: string
  description: string
  world_id: string
  admin_id: string
  member_ids: string[]
  max_players: number
  is_active: boolean
  game_state: 'waiting' | 'character_selection' | 'playing' | 'finished'
  current_chapter: number
  ready_players: string[]
  selected_characters: Array<{
    user_id: string
    character_id: string
  }>
  chapters: Chapter[]
  members: Member[]
  created_at: string
}

export interface Chapter {
  chapter_number: number
  title: string
  content: string
  created_at: string
}

export interface Member {
  user_id: string
  username: string
  is_ready: boolean
  selected_character?: {
    character_id: string
    character_name: string
  }
}

export interface CreateRoomRequest {
  name: string
  description: string
  world_id: string
  max_players: number
}

export interface UpdateRoomRequest {
  name?: string
  description?: string
  max_players?: number
}

export interface WebSocketMessage {
  type: string
  data?: any
}

class ApiGame {
  // Get all rooms
  async getRooms(): Promise<Room[]> {
    const response = await apiClient.get('/rooms')
    return response.data
  }

  // Get room by ID
  async getRoom(roomId: string): Promise<Room> {
    const response = await apiClient.get(`/rooms/${roomId}`)
    return response.data
  }

  // Create new room
  async createRoom(roomData: CreateRoomRequest): Promise<Room> {
    const response = await apiClient.post('/rooms', roomData)
    return response.data
  }

  // Update room
  async updateRoom(roomId: string, roomData: UpdateRoomRequest): Promise<Room> {
    const response = await apiClient.put(`/rooms/${roomId}`, roomData)
    return response.data
  }

  // Delete room
  async deleteRoom(roomId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/rooms/${roomId}`)
    return response.data
  }

  // Join room
  async joinRoom(roomId: string): Promise<Room> {
    const response = await apiClient.post(`/rooms/${roomId}/join`)
    return response.data
  }

  // Leave room
  async leaveRoom(roomId: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/rooms/${roomId}/leave`)
    return response.data
  }

  // Select character in room
  async selectCharacter(roomId: string, characterId: string): Promise<Room> {
    const response = await apiClient.post(`/rooms/${roomId}/select-character`, {
      character_id: characterId
    })
    return response.data
  }

  // Toggle ready status
  async toggleReady(roomId: string): Promise<Room> {
    const response = await apiClient.post(`/rooms/${roomId}/toggle-ready`)
    return response.data
  }

  // Start game
  async startGame(roomId: string): Promise<Room> {
    const response = await apiClient.post(`/rooms/${roomId}/start`)
    return response.data
  }

  // Create WebSocket connection
  createWebSocket(roomId: string, token: string): WebSocket {
    const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000'
    const wsUrl = `${wsBaseUrl}/api/ws/${roomId}?token=${token}`
    return new WebSocket(wsUrl)
  }

  // Game Management APIs
  
  // Get game by ID
  async getGame(gameId: string): Promise<any> {
    const response = await apiClient.get(`/games/${gameId}`)
    return response.data
  }

  // Get game chapters
  async getChapters(gameId: string): Promise<any> {
    const response = await apiClient.get(`/games/${gameId}/chapters`)
    return response.data
  }

  // Get game messages
  async getMessages(gameId: string, limit = 50, offset = 0): Promise<any> {
    const response = await apiClient.get(`/games/${gameId}/messages`, {
      params: { limit, offset }
    })
    return response.data
  }

  // Get game actions
  async getActions(gameId: string, status?: string): Promise<any> {
    const response = await apiClient.get(`/games/${gameId}/actions`, {
      params: status ? { status } : {}
    })
    return response.data
  }

  // Mark ready to continue
  async markContinue(gameId: string, payload: { ready: boolean }): Promise<any> {
    const response = await apiClient.post(`/games/${gameId}/continue`, payload)
    return response.data
  }

  // Propose action
  async proposeAction(gameId: string, payload: { action: string; character_id?: string; chapter_number?: number }): Promise<any> {
    const response = await apiClient.post(`/games/${gameId}/actions`, payload)
    return response.data
  }

  // Post message
  async postMessage(gameId: string, payload: { message: string; message_type?: string }): Promise<any> {
    const response = await apiClient.post(`/games/${gameId}/messages`, payload)
    return response.data
  }

  // Get my games
  async getMyGames(): Promise<any> {
    const response = await apiClient.get('/games/my')
    return response.data
  }

  // Leave game
  async leaveGame(gameId: string): Promise<any> {
    const response = await apiClient.post(`/games/${gameId}/leave`)
    return response.data
  }

  // Update game settings (admin only)
  async updateSettings(gameId: string, settings: {
    discussion_time?: number
    auto_continue?: boolean
    continue_time?: number
    require_all_players?: boolean
    allow_suggestions?: boolean
    max_chapters?: number
  }): Promise<any> {
    const response = await apiClient.patch(`/games/${gameId}/settings`, settings)
    return response.data
  }
}

export const apiGame = new ApiGame()
export default apiGame
