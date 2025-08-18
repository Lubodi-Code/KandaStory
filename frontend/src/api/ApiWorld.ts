import { apiClient } from '../lib/api'

export interface World {
  _id: string
  name: string
  description: string
  theme: string
  setting: string
  tone: string
  created_at: string
}

class ApiWorld {
  // Get all worlds
  async getWorlds(): Promise<World[]> {
    const response = await apiClient.get('/worlds')
    return response.data
  }

  // Get world by ID
  async getWorld(worldId: string): Promise<World> {
    const response = await apiClient.get(`/worlds/${worldId}`)
    return response.data
  }
}

export const apiWorld = new ApiWorld()
export default apiWorld
