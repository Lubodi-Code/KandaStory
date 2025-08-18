<template>
  <div class="p-6">
    <div class="max-w-7xl mx-auto app-noise">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gold-400">Mis Personajes</h1>
      <button
        @click="showCreateForm = !showCreateForm"
        class="btn-gold"
      >
        {{ showCreateForm ? 'Cancelar' : 'Crear Personaje' }}
      </button>
    </div>

    <!-- Character Creation Form -->
  <div v-if="showCreateForm" class="card-navy card-accent p-6 rounded-lg shadow-md mb-6">
      <h2 class="text-xl font-semibold mb-4 text-gold-300">Crear Nuevo Personaje</h2>
      
      <!-- Step 1: Character Form -->
      <div v-if="!evaluationResult">
        <form @submit.prevent="evaluateCharacter">
          <div class="mb-4">
            <label class="block text-sm font-medium text-emerald-200 mb-2">Nombre</label>
            <input
              v-model="newCharacter.name"
              type="text"
              required
              class="w-full px-3 py-2 border border-emerald-800 rounded-md bg-navy-900/40 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Rasgos Físicos</label>
              <TraitInput v-model="newCharacter.physical" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Rasgos Mentales</label>
              <TraitInput v-model="newCharacter.mental" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Habilidades</label>
              <TraitInput v-model="newCharacter.skills" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Defectos</label>
              <TraitInput v-model="newCharacter.flaws" />
            </div>
          </div>
          
          <!-- New fields -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-emerald-200 mb-2">Historia/Transfondo</label>
            <textarea
              v-model="newCharacter.background"
              rows="3"
              placeholder="Historia del personaje, su pasado, origen..."
              class="w-full px-3 py-2 border border-emerald-800 rounded-md bg-navy-900/40 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            ></textarea>
          </div>
          
          <div class="mb-4">
            <label class="block text-sm font-medium text-emerald-200 mb-2">Creencias y Aspiraciones</label>
            <textarea
              v-model="newCharacter.beliefs"
              rows="3"
              placeholder="¿En qué cree? ¿Cuáles son sus objetivos y motivaciones?"
              class="w-full px-3 py-2 border border-emerald-800 rounded-md bg-navy-900/40 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            ></textarea>
          </div>
          
          <div class="flex space-x-4">
            <button
              type="submit"
              :disabled="loading"
              class="btn-gold"
            >
              {{ loading ? 'Evaluando...' : 'Evaluar con IA' }}
            </button>
            <button
              type="button"
              @click="createCharacterDirectly"
              :disabled="loading"
              class="btn-outline"
            >
              {{ loading ? 'Creando...' : 'Crear sin Evaluación' }}
            </button>
          </div>
        </form>
      </div>

      <!-- Step 2: AI Evaluation and Corrections -->
      <div v-if="evaluationResult && !finalizing">
        <div class="mb-6 p-4 bg-blue-900/40 border border-blue-800 text-blue-100 rounded-lg">
          <h3 class="font-semibold text-blue-200 mb-2">Evaluación de IA:</h3>
          <p class="text-blue-100">{{ evaluationResult.evaluation_text }}</p>
        </div>

        <div v-if="evaluationResult.needs_improvement" class="mb-6">
          <h3 class="font-semibold mb-4">Correcciones Sugeridas por IA:</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <!-- Original vs Suggested -->
            <div class="space-y-4">
                <h4 class="font-medium text-gray-200">Versión Original:</h4>
                <div class="bg-red-900/30 p-4 rounded border border-red-800 text-red-100">
                  <CharacterPreview :character="newCharacter" />
                </div>
              </div>
            
            <div class="space-y-4">
              <h4 class="font-medium text-gray-200">Versión Corregida por IA:</h4>
              <div class="bg-green-900/30 p-4 rounded border border-green-800 text-green-100">
                <CharacterPreview :character="evaluationResult.suggested_corrections" />
              </div>
            </div>
          </div>

          <div class="flex space-x-4 mt-6">
            <button
              @click="acceptSuggestions"
              :disabled="finalizing"
              class="btn"
            >
              {{ finalizing ? 'Creando...' : 'Usar Versión Corregida' }}
            </button>
            <button
              @click="editCorrectedCharacter"
              class="btn-outline"
            >
              Editar Versión Corregida
            </button>
            <button
              @click="goBackToEdit"
              class="btn-outline"
            >
              Editar Versión Original
            </button>
          </div>
        </div>

        <div v-else class="mb-6">
          <div class="bg-green-50 p-4 rounded border border-green-200">
            <p class="text-green-700">¡El personaje está bien diseñado! Puedes crearlo directamente o hacer ajustes.</p>
          </div>
          <div class="flex space-x-4 mt-4">
            <button
              @click="createCharacterDirectly"
              :disabled="finalizing"
              class="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {{ finalizing ? 'Creando...' : 'Crear Personaje' }}
            </button>
            <button
              @click="goBackToEdit"
              class="bg-gray-600 text-white px-6 py-2 rounded hover:bg-gray-700"
            >
              Hacer Ajustes
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Characters List -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
  v-for="(character, idx) in characters"
  :key="character._id || `char-${idx}`"
        :class="[
          'p-5 rounded-xl cursor-pointer transition transform',
          selectedCharacter === idx
            ? 'bg-emerald-700 text-white shadow-2xl scale-100 border-0'
            : 'bg-neutral-800/80 text-white border border-emerald-700/10 shadow hover:shadow-lg hover:-translate-y-0.5'
        ]"
        @click="selectedCharacter = idx"
      >
        <div class="flex justify-between items-center mb-2">
          <h3 class="text-lg font-bold text-emerald-50">{{ character.name }}</h3>
          <button @click.stop="editCharacter(character)" class="btn-outline px-3 py-1 text-sm">Editar</button>
        </div>
        
        <div class="text-sm text-emerald-100 leading-relaxed mb-2">
          <div v-if="character.physical"><strong class="text-emerald-200">Físico:</strong> {{ (character.physical || []).map(t => t.name).join(', ') }}</div>
          <div v-if="character.mental"><strong class="text-emerald-200">Mental:</strong> {{ (character.mental || []).map(t => t.name).join(', ') }}</div>
          <div v-if="character.skills"><strong class="text-emerald-200">Habilidades:</strong> {{ (character.skills || []).map(t => t.name).join(', ') }}</div>
          <div v-if="character.flaws"><strong class="text-emerald-200">Defectos:</strong> {{ (character.flaws || []).map(t => t.name).join(', ') }}</div>
          <div v-if="character.background"><strong class="text-emerald-200">Historia:</strong> {{ character.background.substring(0, 120) }}...</div>
          <div v-if="character.beliefs"><strong class="text-emerald-200">Creencias:</strong> {{ character.beliefs.substring(0, 120) }}...</div>
        </div>
        
        <div v-if="character.evaluation" class="mt-4 p-3 bg-yellow-900/30 border border-yellow-800 rounded text-yellow-100">
          <h4 class="font-medium text-yellow-200 mb-1">Evaluación IA:</h4>
          <p class="text-sm text-yellow-100">{{ character.evaluation }}</p>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'
import TraitInput from '../components/TraitInput.vue'
import CharacterPreview from '../components/CharacterPreview.vue'
import { useCharactersStore } from '../stores/characters'
import { useAuthStore } from '../stores/auth'
import { apiClient } from '../lib/api'

const charactersStore = useCharactersStore()
const router = useRouter()
const authStore = useAuthStore()
// State from store (ensure reactivity with storeToRefs)
const { myCharacters: characters } = storeToRefs(charactersStore)

// Local component state
const showCreateForm = ref(false)
const loading = ref(false)
const finalizing = ref(false)
const evaluationResult = ref<EvaluationResult | null>(null)

interface Trait {
  name: string
  description?: string
}

interface Trait { name: string; description?: string }
interface Character {
  _id?: string
  id?: string
  name: string
  physical: Trait[]
  mental: Trait[]
  skills: Trait[]
  flaws: Trait[]
  background?: string
  beliefs?: string
  owner_id?: string
  created_at?: string
}

interface EvaluationResult {
  evaluation_text: string
  suggested_corrections: any
  needs_improvement: boolean
}

const newCharacter = ref<Character>({
  name: '',
  physical: [],
  mental: [],
  skills: [],
  flaws: [],
  background: '',
  beliefs: ''
})

// Editing state: when set, form will update existing character
const editingCharacterId = ref<string | null>(null)

// Selección local de personaje (index)
const selectedCharacter = ref<number | null>(null)

// Functions using store
async function loadCharacters() {
  await charactersStore.loadMyCharacters()
}

async function evaluateCharacter() {
  loading.value = true
  try {
    const response = await apiClient.post('/characters/evaluate', newCharacter.value)
    evaluationResult.value = response.data
  } catch (error: any) {
    console.error('Error evaluating character:', error)
    alert(error.response?.data?.detail || 'Error al evaluar personaje')
  } finally {
    loading.value = false
  }
}

async function acceptSuggestions() {
  finalizing.value = true
  try {
    const payload = evaluationResult.value!.suggested_corrections
    if (editingCharacterId.value) {
      // Update existing character
      const updated = await charactersStore.updateCharacter(editingCharacterId.value, payload)
      // Replace locally
      const idx = characters.value.findIndex(c => c._id === editingCharacterId.value)
      if (idx !== -1) characters.value[idx] = updated
    } else {
      const response = await apiClient.post('/characters', payload)
      characters.value.push(response.data)
    }
    resetForm()
  } catch (error: any) {
    console.error('Error creating character:', error)
    alert(error.response?.data?.detail || 'Error al crear personaje')
  } finally {
    finalizing.value = false
  }
}

async function createCharacterDirectly() {
  finalizing.value = true
  try {
    if (editingCharacterId.value) {
      const updated = await charactersStore.updateCharacter(editingCharacterId.value, newCharacter.value)
      const idx = characters.value.findIndex(c => c._id === editingCharacterId.value)
      if (idx !== -1) characters.value[idx] = updated
      resetForm()
    } else {
      const response = await apiClient.post('/characters', newCharacter.value)
      characters.value.push(response.data)
      resetForm()
    }
  } catch (error: any) {
    console.error('Error creating character:', error)
    alert(error.response?.data?.detail || 'Error al crear personaje')
  } finally {
    finalizing.value = false
  }
}

function editCorrectedCharacter() {
  // Reemplazar el personaje actual con la versión corregida para editar
  const corrected = evaluationResult.value!.suggested_corrections
  newCharacter.value = {
    name: corrected.name,
    physical: corrected.physical,
    mental: corrected.mental,
    skills: corrected.skills,
    flaws: corrected.flaws,
    background: corrected.background || '',
    beliefs: corrected.beliefs || ''
  }
  evaluationResult.value = null
}

function goBackToEdit() {
  evaluationResult.value = null
}

function resetForm() {
  showCreateForm.value = false
  evaluationResult.value = null
  editingCharacterId.value = null
  newCharacter.value = {
    name: '',
    physical: [],
    mental: [],
    skills: [],
    flaws: [],
    background: '',
    beliefs: ''
  }
}

function editCharacter(character: Character) {
  // Prefill form with existing character for editing
  newCharacter.value = {
    name: character.name,
    physical: character.physical || [],
    mental: character.mental || [],
    skills: character.skills || [],
    flaws: character.flaws || [],
    background: character.background || '',
    beliefs: character.beliefs || ''
  }
  editingCharacterId.value = character._id ?? null
  showCreateForm.value = true
  // Scroll to form or focus could be added here
}

onMounted(async () => {
  // Ensure user is authenticated before loading characters
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  try {
    await loadCharacters()
  } catch (error: any) {
    console.error('Error loading characters:', error)
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
    }
  }
})
</script>
