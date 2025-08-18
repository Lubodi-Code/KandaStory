import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiClient } from '../lib/api'

export interface World {
  _id: string
  title: string
  summary: string
  context: string
  logic: string
  time_period: string
  space_setting: string
  is_public: boolean
  allow_action_suggestions: boolean
  creator_id: string
  created_at: string
  usage_count: number
}

export interface WorldsResponse {
  my_worlds: World[]
  public_worlds: World[]
}

export const useWorldsStore = defineStore('worlds', () => {
  const myWorlds = ref<World[]>([])
  const publicWorlds = ref<World[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function loadWorlds() {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.get<WorldsResponse>('/worlds')
      myWorlds.value = response.data.my_worlds
      publicWorlds.value = response.data.public_worlds
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error loading worlds'
      console.error('Error loading worlds:', err)
    } finally {
      loading.value = false
    }
  }

  async function createWorld(worldData: Partial<World>) {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.post('/worlds', worldData)
      const newWorld = response.data
      myWorlds.value.push(newWorld)
      return newWorld
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error creating world'
      console.error('Error creating world:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getWorldById(worldId: string) {
    try {
      const response = await apiClient.get(`/worlds/${worldId}`)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error getting world'
      console.error('Error getting world:', err)
      throw err
    }
  }

  async function updateWorld(worldId: string, worldData: Partial<World>) {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.put(`/worlds/${worldId}`, worldData)
      const updatedWorld = response.data
      
      // Update in myWorlds if it exists there
      const index = myWorlds.value.findIndex(w => w._id === worldId)
      if (index !== -1) {
        myWorlds.value[index] = updatedWorld
      }
      
      return updatedWorld
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error updating world'
      console.error('Error updating world:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteWorld(worldId: string) {
    loading.value = true
    error.value = null
    try {
      await apiClient.delete(`/worlds/${worldId}`)
      
      // Remove from myWorlds
      myWorlds.value = myWorlds.value.filter(w => w._id !== worldId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error deleting world'
      console.error('Error deleting world:', err)
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
    myWorlds,
    publicWorlds,
    loading,
    error,
    
    // Actions
    loadWorlds,
    createWorld,
    getWorldById,
    updateWorld,
    deleteWorld,
    clearError
  }
})
