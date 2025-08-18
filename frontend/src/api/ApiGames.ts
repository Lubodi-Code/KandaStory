import { apiClient } from '../lib/api'

export interface GameSettings {
  allow_suggestions: boolean
  discussion_time: number
  auto_continue: boolean
  continue_time: number
}

export interface GameMeta {
  _id: string
  room_id: string
  name: string
  world_id: string
  max_chapters: number
  max_players: number
  settings: GameSettings
  owner_id: string
  admin_id: string
  current_chapter: number
  game_state: 'playing' | 'discussion' | 'finished' | 'action_phase'
  created_at?: string
  current_deadline?: string | null
}

export interface GameMemberDoc {
  _id?: string
  game_id: string
  user_id: string
  character_id?: string | null
  role: 'player' | 'admin'
  joined_at?: string
  is_ready: boolean
}

export interface GameMessageDoc {
  _id?: string
  game_id: string
  chapter_id?: string | null
  user_id: string
  content: string
  type: 'chat' | 'system' | 'action'
  timestamp?: string
}

export interface GameActionDoc {
  _id?: string
  game_id: string
  user_id: string
  character_id?: string | null
  action: string
  status: 'pending' | 'approved' | 'rejected'
  created_at?: string
  chapter_id?: string | null
}

export interface GameChapterDoc {
  _id?: string
  game_id: string
  chapter_number: number
  content: string
  created_at?: string
  created_by?: string
}

class ApiGames {
  async markContinue(gameId: string, ready: boolean = true) {
    const { data } = await apiClient.post(`/games/${gameId}/continue`, { ready })
    return data as { ok: boolean }
  }
  async createFromRoom(roomId: string): Promise<GameMeta> {
    const { data } = await apiClient.post(`/games/from-room/${roomId}`)
    return data
  }

  async get(gameId: string): Promise<GameMeta> {
    const { data } = await apiClient.get(`/games/${gameId}`)
    return data
  }

  async members(gameId: string) {
    const { data } = await apiClient.get(`/games/${gameId}/members`)
    return data as GameMemberDoc[]
  }

  async postMessage(gameId: string, msg: Omit<GameMessageDoc, 'game_id' | 'user_id' | 'timestamp' | '_id'>) {
    const { data } = await apiClient.post(`/games/${gameId}/messages`, msg)
    return data as GameMessageDoc
  }

  async listMessages(gameId: string, limit = 50, offset = 0) {
    const { data } = await apiClient.get(`/games/${gameId}/messages`, { params: { limit, offset }})
    return data as GameMessageDoc[]
  }

  async proposeAction(gameId: string, action: Omit<GameActionDoc, 'game_id' | 'user_id' | 'created_at' | '_id' | 'status'>) {
    const { data } = await apiClient.post(`/games/${gameId}/actions`, action)
    return data as GameActionDoc
  }

  async listActions(gameId: string, status?: 'pending' | 'approved' | 'rejected') {
    const { data } = await apiClient.get(`/games/${gameId}/actions`, { params: { status }})
    return data as GameActionDoc[]
  }

  async addChapter(gameId: string, ch: Omit<GameChapterDoc, 'game_id' | '_id' | 'created_at' | 'created_by'>) {
    const { data } = await apiClient.post(`/games/${gameId}/chapters`, ch)
    return data as GameChapterDoc
  }

  async listChapters(gameId: string) {
    const { data } = await apiClient.get(`/games/${gameId}/chapters`)
    return data as GameChapterDoc[]
  }

  async leave(gameId: string) {
    const { data } = await apiClient.post(`/games/${gameId}/leave`)
    return data as { ok: boolean; message: string }
  }
}

export const apiGames = new ApiGames()
export default apiGames
