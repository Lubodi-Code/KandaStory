<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-60 flex justify-center items-center z-50">
    <div class="card-navy border rounded-lg shadow-2xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto text-slate-100">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold text-gold-300">Crear Nueva Sala</h3>
        <button @click="closeForm" class="text-slate-300 hover:text-emerald-200" aria-label="Cerrar formulario">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Loading state -->
      <div v-if="isLoadingWorlds" class="text-center py-8">
        <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-400"></div>
        <p class="mt-2 text-sm text-slate-300">Cargando mundos...</p>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Nombre de la sala -->
        <div>
          <label class="block text-sm font-medium text-emerald-200 mb-1">
            Nombre de la Sala <span class="text-rose-500">*</span>
          </label>
          <input
            v-model="formData.name"
            type="text"
            required
            maxlength="50"
            placeholder="Ej: La Taberna del Dragón Dorado"
            class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100 placeholder:text-slate-400"
          />
        </div>

        <!-- Mundo -->
        <div>
          <label class="block text-sm font-medium text-emerald-200 mb-1">
            Mundo <span class="text-red-500">*</span>
          </label>
          <select
            v-model="formData.world_id"
            required
            class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100"
          >
            <option value="">Selecciona un mundo</option>
            <optgroup v-if="(myWorlds || []).length" label="Mis Mundos">
              <option v-for="world in (myWorlds || [])" :key="world._id" :value="world._id">
                {{ world.title }} - {{ world.time_period }}
              </option>
            </optgroup>
            <optgroup v-if="(publicWorlds || []).length" label="Mundos Públicos">
              <option v-for="world in (publicWorlds || [])" :key="world._id" :value="world._id">
                {{ world.title }} - {{ world.time_period }}
              </option>
            </optgroup>
          </select>
          <div v-if="!hasWorlds" class="mt-2">
            <router-link
              to="/worlds"
              class="text-sm text-emerald-300 hover:text-emerald-200 underline"
            >
              Crear un mundo primero
            </router-link>
          </div>
        </div>

        <!-- Descripción del mundo seleccionado -->
  <div v-if="selectedWorld" class="p-3 bg-navy-900/40 border border-emerald-800 rounded-md">
          <h4 class="font-medium text-sm text-emerald-200 mb-1">{{ selectedWorld.title }}</h4>
          <p class="text-xs text-slate-300">{{ selectedWorld.description }}</p>
          <div class="flex items-center space-x-2 mt-2 text-xs text-slate-400">
            <span>{{ selectedWorld.time_period }}</span>
            <span>•</span>
            <span>{{ selectedWorld.genre }}</span>
          </div>
        </div>

        <!-- Máximo de jugadores -->
        <div>
          <label class="block text-sm font-medium text-emerald-200 mb-1">
            Máximo de Jugadores
          </label>
          <select
            v-model.number="formData.max_players"
            class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100"
          >
            <option :value="2">2 jugadores</option>
            <option :value="3">3 jugadores</option>
            <option :value="4">4 jugadores</option>
            <option :value="5">5 jugadores</option>
            <option :value="6">6 jugadores</option>
          </select>
        </div>

        <!-- Máximo de capítulos -->
        <div>
          <label class="block text-sm font-medium text-emerald-200 mb-1">
            Máximo de Capítulos
          </label>
          <input
            v-model.number="formData.max_chapters"
            type="number"
            min="1"
            max="20"
            required
            class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100"
          />
          <p class="text-xs text-slate-400 mt-1">Máximo permitido: 20 capítulos.</p>
        </div>

        <!-- Configuración avanzada -->
          <div class="border-t border-emerald-800 pt-4">
          <h4 class="font-medium text-sm text-emerald-200 mb-3">Configuración de Juego</h4>
          
          <div class="space-y-3">
            <div>
              <label class="block text-sm text-slate-300 mb-1">
                Tiempo de discusión (segundos)
              </label>
              <input
                v-model.number="formData.discussion_time"
                type="number"
                min="30"
                max="600"
                class="w-full px-3 py-2 bg-gray-800 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100"
              />
            </div>

            <div>
              <label class="flex items-center space-x-2">
                <input
                  v-model="formData.auto_continue"
                  type="checkbox"
                  class="rounded bg-navy-900/40 border-emerald-700"
                />
                <span class="text-sm text-slate-300">Continuar automáticamente</span>
              </label>
            </div>

            <div v-if="!formData.auto_continue">
              <label class="block text-sm text-slate-300 mb-1">
                Tiempo para continuar (segundos)
              </label>
              <input
                v-model.number="formData.continue_time"
                type="number"
                min="10"
                max="300"
                class="w-full px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500 text-slate-100"
              />
            </div>
          </div>
        </div>

        <!-- Botones -->
        <div class="flex space-x-3 pt-4">
          <button
            type="submit"
            :disabled="isCreating || !canCreate"
            class="flex-1 btn-gold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isCreating ? 'Creando...' : 'Crear Sala' }}
          </button>
          <button
            type="button"
            @click="closeForm"
            class="btn-outline"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../lib/api'

interface World {
  _id: string
  title: string
  description: string
  time_period: string
  genre: string
}

interface CreateRoomData {
  name: string
  world_id: string
  max_players: number
  max_chapters: number
  discussion_time: number
  auto_continue: boolean
  continue_time: number
}

const props = defineProps<{
  show: boolean
  preselectedWorldId?: string
}>()

const emit = defineEmits<{
  close: []
  created: [roomId: string]
}>()

const router = useRouter()

// Form data
const formData = ref<CreateRoomData>({
  name: '',
  world_id: '',
  max_players: 4,
  max_chapters: 5,
  discussion_time: 120,
  auto_continue: false,
  continue_time: 60
})

// State
const myWorlds = ref<World[]>([])
const publicWorlds = ref<World[]>([])
const isLoadingWorlds = ref(false)
const isCreating = ref(false)

// Computed
const hasWorlds = computed(() => 
  (myWorlds.value?.length || 0) + (publicWorlds.value?.length || 0) > 0
)

const selectedWorld = computed(() => {
  const allWorlds = [...(myWorlds.value || []), ...(publicWorlds.value || [])]
  return allWorlds.find(w => w._id === formData.value.world_id) || null
})

const canCreate = computed(() => 
  formData.value.name.trim() && formData.value.world_id && hasWorlds.value
)

// Watch for preselected world
watch(() => props.preselectedWorldId, (worldId) => {
  if (worldId) {
    formData.value.world_id = worldId
  }
}, { immediate: true })

// Methods
async function loadWorlds() {
  if ((myWorlds.value?.length || 0) > 0 || (publicWorlds.value?.length || 0) > 0) return
  
  isLoadingWorlds.value = true
  try {
    const [myResponse, publicResponse] = await Promise.allSettled([
      apiClient.get('/worlds'),
      apiClient.get('/worlds/public')
    ])
    
    if (myResponse.status === 'fulfilled') {
      const data = myResponse.value.data
      myWorlds.value = data?.my_worlds || data || []
      // Si viene en formato combinado, usar public_worlds de ahí también
      if (data?.public_worlds && !publicWorlds.value?.length) {
        publicWorlds.value = data.public_worlds
      }
    } else {
      myWorlds.value = []
    }
    
    if (publicResponse.status === 'fulfilled' && !publicWorlds.value?.length) {
      publicWorlds.value = publicResponse.value.data || []
    } else if (publicResponse.status === 'rejected' && !publicWorlds.value?.length) {
      publicWorlds.value = []
    }
  } catch (error) {
    console.error('Error loading worlds:', error)
    myWorlds.value = []
    publicWorlds.value = []
  } finally {
    isLoadingWorlds.value = false
  }
}

async function handleSubmit() {
  if (!canCreate.value || isCreating.value) return
  
  isCreating.value = true
  try {
    const { data } = await apiClient.post('/rooms', formData.value)
    const roomId = data?._id || data?.id
    
    if (roomId) {
      emit('created', roomId)
      closeForm()
      router.push(`/rooms/${roomId}`)
    }
  } catch (error: any) {
    console.error('Error creating room:', error)
    alert(error?.response?.data?.detail || 'Error al crear la sala')
  } finally {
    isCreating.value = false
  }
}

function closeForm() {
  // Reset form
  formData.value = {
    name: '',
    world_id: props.preselectedWorldId || '',
    max_players: 4,
  max_chapters: 5,
    discussion_time: 120,
    auto_continue: false,
    continue_time: 60
  }
  emit('close')
}

// Watch show prop to load worlds when opened
watch(() => props.show, (show) => {
  if (show) {
    loadWorlds()
  }
})
</script>
