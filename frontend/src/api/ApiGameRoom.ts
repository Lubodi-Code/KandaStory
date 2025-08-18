// Legacy file: replaced by Rooms (/rooms) and Games (/games) APIs.
// Kept as a minimal compatibility wrapper to avoid build-time 404 calls.
import { apiClient } from '../lib/api'

export default class ApiGameRoom {
  static async getGameRoom(roomId: string) { return (await apiClient.get(`/rooms/${roomId}`)).data }
  static async joinGameRoom(roomId: string) { return (await apiClient.post(`/rooms/${roomId}/join`)).data }
  static async leaveGameRoom(roomId: string) { return (await apiClient.post(`/rooms/${roomId}/leave`)).data }
  static async selectCharacter(roomId: string, characterId: string) { return (await apiClient.post(`/rooms/${roomId}/select-character`, { character_id: characterId })).data }
  static async setPlayerReady(roomId: string, ready = true) { return (await apiClient.post(`/rooms/${roomId}/ready`, { ready })).data }
  static async startGame(roomId: string) { return (await apiClient.post(`/rooms/${roomId}/start-game`)).data }
}
