// Export all API services
export { apiAuth, type LoginRequest, type RegisterRequest, type LoginResponse, type User } from './ApiAuth'
export { apiCharacter, type Character, type CreateCharacterRequest, type UpdateCharacterRequest } from './ApiCharacter'
export { apiWorld, type World } from './ApiWorld'
export { apiGames, type GameMeta, type GameSettings, type GameMemberDoc, type GameMessageDoc, type GameActionDoc, type GameChapterDoc } from './ApiGames'
export { apiRooms, type RoomPublic } from './ApiRooms'
export { apiGame as ApiGame, type Room } from './ApiGame'

// Export API client
export { apiClient } from '../lib/api'
