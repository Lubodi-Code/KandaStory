import { apiClient } from '../lib/api'

export interface Character {
  _id: string
  name: string
  description: string
  traits: string[]
  world_id: string
  user_id: string
  created_at: string
}

export interface CreateCharacterRequest {
  name: string
  description: string
  traits: string[]
  world_id: string
}

export interface UpdateCharacterRequest {
  name?: string
  description?: string
  traits?: string[]
}

class ApiCharacter {
  // Get all characters for current user
  async getUserCharacters(): Promise<Character[]> {
    const response = await apiClient.get('/characters')
    return response.data
  }

  // Get character by ID
  async getCharacter(characterId: string): Promise<Character> {
    const response = await apiClient.get(`/characters/${characterId}`)
    return response.data
  }

  // Create new character
  async createCharacter(characterData: CreateCharacterRequest): Promise<Character> {
    const response = await apiClient.post('/characters', characterData)
    return response.data
  }

  // Update character
  async updateCharacter(characterId: string, characterData: UpdateCharacterRequest): Promise<Character> {
    const response = await apiClient.put(`/characters/${characterId}`, characterData)
    return response.data
  }

  // Delete character
  async deleteCharacter(characterId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/characters/${characterId}`)
    return response.data
  }

  // Get characters by world
  async getCharactersByWorld(worldId: string): Promise<Character[]> {
    const response = await apiClient.get(`/characters/world/${worldId}`)
    return response.data
  }
}

export const apiCharacter = new ApiCharacter()
export default apiCharacter
