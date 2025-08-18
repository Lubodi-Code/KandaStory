import { apiClient } from '../lib/api'

export interface RoomPublic {
  _id: string
  id?: string
  name: string
  world_id?: string | null
  world?: any
  max_players: number
  game_state: 'waiting' | 'playing' | 'discussion' | 'finished' | 'action_phase'
  current_members?: number
  is_joinable?: boolean
  is_user_member?: boolean
  admin_id?: string
  member_ids?: string[]
  ready_players?: string[]
  selected_characters?: any[]
  current_chapter?: number
  chapters?: string[]
  messages?: any[]
  created_at?: string
  game_id?: string | null
}

class ApiRooms {
  async list(): Promise<RoomPublic[]> {
    const token = localStorage.getItem('token')
    const endpoint = token ? '/rooms' : '/rooms/public'
    const { data } = await apiClient.get(endpoint)
    return data
  }

  async get(roomId: string): Promise<RoomPublic> {
    const { data } = await apiClient.get(`/rooms/${roomId}`)
    return data
  }

  async create(payload: { name: string; world_id: string; max_chapters?: number; max_players?: number; allow_suggestions?: boolean; discussion_time?: number; auto_continue?: boolean; continue_time?: number; }) {
    const { data } = await apiClient.post('/rooms', payload)
    return data as RoomPublic
  }

  async join(roomId: string) {
    const { data } = await apiClient.post(`/rooms/${roomId}/join`)
    return data as { joined: boolean; message?: string }
  }

  async leave(roomId: string) {
    const { data } = await apiClient.post(`/rooms/${roomId}/leave`)
    return data as { left: boolean; message?: string }
  }

  async selectCharacter(roomId: string, characterId: string) {
    const { data } = await apiClient.post(`/rooms/${roomId}/select-character`, { character_id: characterId })
    return data
  }

  async toggleReady(roomId: string) {
    // Prefer WS 'toggle_ready' in UI; REST kept for compatibility if needed
    const { data } = await apiClient.post(`/rooms/${roomId}/ready`)
    return data as { is_ready: boolean; ready_count: number; total_members: number }
  }

  async startGame(roomId: string) {
    const { data } = await apiClient.post(`/rooms/${roomId}/start-game`)
    return data as { message: string; game_id?: string }
  }
}

export const apiRooms = new ApiRooms()
export default apiRooms
