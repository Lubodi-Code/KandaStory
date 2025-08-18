<template>
  <div class="p-6">
    <div class="max-w-7xl mx-auto app-noise">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gold-400">Mundos y Series</h1>
      <button
        @click="showCreateForm = !showCreateForm"
        class="btn-gold"
      >
        {{ showCreateForm ? 'Cancelar' : 'Crear Mundo' }}
      </button>
    </div>

    <!-- World Creation Form -->
    <div v-if="showCreateForm" class="card-navy card-accent p-6 rounded-lg shadow-md mb-6">
      <h2 class="text-xl font-semibold mb-4 text-gold-300">Crear Nuevo Mundo/Serie</h2>
      <form @submit.prevent="createWorld">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
              <label class="block text-sm font-medium text-emerald-200 mb-2">Título</label>
            <input
              v-model="newWorld.title"
              type="text"
              required
              placeholder="ej. Reino de Eldoria"
              class="w-full px-3 py-2 border border-emerald-800 rounded-md bg-navy-900/40 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-emerald-200 mb-2">Período de Tiempo</label>
            <input
              v-model="newWorld.time_period"
              type="text"
              required
              placeholder="ej. Medieval mágico, Futuro distópico"
              class="w-full px-3 py-2 border border-emerald-800 rounded-md bg-navy-900/40 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-emerald-200 mb-2">Resumen</label>
          <textarea
            v-model="newWorld.summary"
            rows="3"
            required
            placeholder="Descripción breve del mundo/serie..."
            class="w-full px-3 py-2 border border-emerald-800 rounded-md bg-navy-900/40 text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          ></textarea>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Contexto del Mundo</label>
          <textarea
            v-model="newWorld.context"
            rows="4"
            required
            placeholder="Describe el mundo en detalle: geografía, historia, sociedades, conflictos..."
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          ></textarea>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Lógica del Mundo</label>
          <textarea
            v-model="newWorld.logic"
            rows="3"
            required
            placeholder="¿Existen poderes sobrenaturales? ¿Qué tecnología está disponible? ¿Cómo funciona la magia?"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          ></textarea>
        </div>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Ambientación Espacial</label>
          <input
            v-model="newWorld.space_setting"
            type="text"
            required
            placeholder="ej. Fantasía épica, Cyberpunk urbano, Western americano"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div class="flex items-center space-x-6 mb-4">
          <label class="flex items-center">
            <input
              v-model="newWorld.is_public"
              type="checkbox"
              class="mr-2"
            />
            <span class="text-sm text-gray-700">Hacer público (otros usuarios podrán usar este mundo)</span>
          </label>
          
          <label class="flex items-center">
            <input
              v-model="newWorld.allow_action_suggestions"
              type="checkbox"
              class="mr-2"
            />
            <span class="text-sm text-gray-700">Permitir sugerencias entre capítulos</span>
          </label>
        </div>
        
        <button
          type="submit"
          :disabled="loading"
          class="btn-gold"
        >
          {{ loading ? 'Creando...' : 'Crear Mundo' }}
        </button>
      </form>
    </div>

    <!-- Worlds List -->
    <div class="space-y-6">
      <!-- My Worlds Section -->
      <div>
    <h2 class="text-xl font-semibold mb-4 text-white">Mis Mundos</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="world in myWorlds"
            :key="world._id"
            class="bg-gradient-to-br from-neutral-800/90 to-neutral-900/80 p-6 rounded-2xl shadow-xl border border-emerald-600/20 transform transition hover:shadow-2xl hover:-translate-y-1"
          >
            <div class="flex justify-between items-start mb-3">
              <h3 class="text-lg font-bold text-emerald-50">{{ world.title }}</h3>
              <span v-if="world.is_public" class="text-xs bg-emerald-600 text-white px-3 py-1 rounded-full">Público</span>
            </div>
            
            <p class="text-sm text-emerald-100 mb-3">{{ world.summary }}</p>
            
            <div class="text-xs text-emerald-200 mb-3 space-y-1">
              <div><strong class="text-emerald-100">Época:</strong> {{ world.time_period }}</div>
              <div><strong class="text-emerald-100">Estilo:</strong> {{ world.space_setting }}</div>
              <div><strong class="text-emerald-100">Usos:</strong> {{ world.usage_count || 0 }}</div>
            </div>

            <div class="flex space-x-3 mt-4">
              <button
                @click="editWorld()"
                class="btn-outline px-4 py-2 text-sm"
              >
                Editar
              </button>
              <button
                @click="useWorldInRoom(world)"
                class="btn-gold px-4 py-2 text-sm"
              >
                Usar en Nueva Sala
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Public Worlds Section -->
      <div>
  <h2 class="text-xl font-semibold mb-4 text-white">Mundos Públicos</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="world in publicWorlds"
            :key="world._id"
            class="bg-gradient-to-br from-neutral-800/90 to-neutral-900/80 p-6 rounded-2xl shadow-xl border border-emerald-600/20 transform transition hover:shadow-2xl hover:-translate-y-1"
          >
            <div class="flex justify-between items-start mb-3">
              <h3 class="text-lg font-bold text-emerald-50">{{ world.title }}</h3>
              <span class="text-xs bg-emerald-600 text-white px-3 py-1 rounded-full">{{ world.usage_count || 0 }} usos</span>
            </div>
            
            <p class="text-sm text-emerald-100 mb-3">{{ world.summary }}</p>
            
            <div class="text-xs text-emerald-200 mb-3">
              <div><strong class="text-emerald-100">Época:</strong> {{ world.time_period }}</div>
              <div><strong class="text-emerald-100">Estilo:</strong> {{ world.space_setting }}</div>
            </div>

            <button
              @click="useWorldInRoom(world)"
              class="btn mt-2 px-4 py-2"
            >
              Usar en Nueva Sala
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorldsStore } from '../stores/worlds'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const worldsStore = useWorldsStore()
const authStore = useAuthStore()

// State from store
const { 
  myWorlds, 
  publicWorlds, 
  loading 
} = worldsStore

// Local component state
const showCreateForm = ref(false)

const newWorld = ref({
  title: '',
  summary: '',
  context: '',
  logic: '',
  time_period: '',
  space_setting: '',
  is_public: false,
  allow_action_suggestions: true
})

// Functions using store
async function loadWorlds() {
  await worldsStore.loadWorlds()
}

async function createWorld() {
  try {
    const worldData = newWorld.value
    
    await worldsStore.createWorld(worldData)
    
    showCreateForm.value = false
    resetForm()
  } catch (error: any) {
    console.error('Error creating world:', error)
    alert(error.response?.data?.detail || 'Error al crear mundo')
  }
}

function resetForm() {
  newWorld.value = {
    title: '',
    summary: '',
    context: '',
    logic: '',
    time_period: '',
    space_setting: '',
    is_public: false,
    allow_action_suggestions: true
  }
}

function editWorld() {
  // TODO: Implementar edición
  alert('Funcionalidad de edición próximamente')
}

function useWorldInRoom(world: any) {
  // Navegar a la creación de sala con el mundo pre-seleccionado
  router.push({
    name: 'rooms',
    query: { world_id: world._id, world_title: world.title }
  })
}

onMounted(async () => {
  // Verificar que el usuario esté autenticado antes de cargar datos
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }
  
  try {
    await loadWorlds()
  } catch (error: any) {
    console.error('Error loading worlds:', error)
    // Si hay error de autenticación, redirigir al login
    if (error.response?.status === 401) {
      authStore.logout()
      router.push('/login')
    }
  }
})
</script>
