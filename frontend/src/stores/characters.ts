import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiClient } from '../lib/api'

export interface Trait { name: string; description?: string }
export interface Character {
  _id: string
  name: string
  physical: Trait[]
  mental: Trait[]
  skills: Trait[]
  flaws: Trait[]
  background?: string
  beliefs?: string
  owner_id?: string
  created_at?: string
  evaluation?: string
}

export const useCharactersStore = defineStore('characters', () => {
  const characters = ref<Character[]>([])
  const myCharacters = ref<Character[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function loadCharacters() {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.get('/characters')
      characters.value = response.data
      myCharacters.value = response.data // Los personajes devueltos ya son del usuario actual
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error loading characters'
      console.error('Error loading characters:', err)
    } finally {
      loading.value = false
    }
  }

  async function loadMyCharacters() {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.get('/characters')
      myCharacters.value = response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error loading my characters'
      console.error('Error loading my characters:', err)
    } finally {
      loading.value = false
    }
  }

  async function createCharacter(characterData: Partial<Character>) {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.post('/characters', characterData)
      const newCharacter = response.data
      characters.value.push(newCharacter)
      myCharacters.value.push(newCharacter)
      return newCharacter
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error creating character'
      console.error('Error creating character:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getCharacterById(characterId: string) {
    try {
      const response = await apiClient.get(`/characters/${characterId}`)
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error getting character'
      console.error('Error getting character:', err)
      throw err
    }
  }

  async function updateCharacter(characterId: string, characterData: Partial<Character>) {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.put(`/characters/${characterId}`, characterData)
      const updatedCharacter = response.data
      
      // Update in characters list
      const index = characters.value.findIndex(c => c._id === characterId)
      if (index !== -1) {
        characters.value[index] = updatedCharacter
      }
      
      // Update in myCharacters list
      const myIndex = myCharacters.value.findIndex(c => c._id === characterId)
      if (myIndex !== -1) {
        myCharacters.value[myIndex] = updatedCharacter
      }
      
      return updatedCharacter
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error updating character'
      console.error('Error updating character:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteCharacter(characterId: string) {
    loading.value = true
    error.value = null
    try {
      await apiClient.delete(`/characters/${characterId}`)
      
      // Remove from characters list
      characters.value = characters.value.filter(c => c._id !== characterId)
      
      // Remove from myCharacters list
      myCharacters.value = myCharacters.value.filter(c => c._id !== characterId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Error deleting character'
      console.error('Error deleting character:', err)
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
    characters,
    myCharacters,
    loading,
    error,
    
    // Actions
    loadCharacters,
    loadMyCharacters,
    createCharacter,
    getCharacterById,
    updateCharacter,
    deleteCharacter,
    clearError
  }
})
