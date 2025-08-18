// Tipos para GameRoom
export interface GameRoom {
  id: string
  name: string
  world_id: string
  world?: World
  admin_id: string
  member_ids: string[]
  members: Player[]
  selected_characters: SelectedCharacter[]
  current_chapter: number
  max_chapters: number
  chapters: string[]
  messages: ChatMessage[]
  game_state: 'waiting' | 'character_selection' | 'playing' | 'discussion' | 'action_phase' | 'finished'
  allow_actions: boolean
  action_time_minutes: number
  pending_actions: PlayerAction[]
  ready_players: string[]
  continue_ready_players?: string[]
  created_at?: string
}

export interface World {
  id: string
  title: string
  summary: string
  context: string
  logic: string
  time_period: string
  space_setting: string
  allow_action_suggestions: boolean
}

export interface Player {
  id: string
  username: string
  email: string
  is_ready: boolean
  selected_character_id?: string
}

export interface SelectedCharacter {
  id: string
  name: string
  physical: Trait[]
  mental: Trait[]
  skills: Trait[]
  flaws: Trait[]
  background?: string
  beliefs?: string
  owner_id: string
  owner_username: string
}

export interface Trait {
  name: string
  description?: string
}

export interface ChatMessage {
  id?: string
  user_id: string
  username: string
  message: string
  timestamp: string
  message_type: 'chat' | 'system' | 'action' | 'story'
}

export interface PlayerAction {
  id?: string
  user_id: string
  username: string
  character_id: string
  character_name: string
  action: string
  timestamp: string
  status: 'pending' | 'approved' | 'rejected'
}

export interface ChapterData {
  chapter_number: number
  content: string
  actions_included: PlayerAction[]
  timestamp: string
}

// Requests
export interface JoinGameRoomRequest {
  // No necesita campos adicionales
}

export interface SelectCharacterRequest {
  character_id: string
}

export interface SetReadyRequest {
  ready: boolean
}

export interface SendChatMessageRequest {
  message: string
  message_type: string
}

export interface ProposeActionRequest {
  character_id: string
  action: string
}

export interface KickPlayerRequest {
  player_id: string
}
