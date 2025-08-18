<template>
  <div>
    <div v-for="(trait, index) in modelValue" :key="index" class="flex items-center mb-3">
      <input
        v-model="trait.name"
        type="text"
        placeholder="Nombre del rasgo"
        class="flex-1 px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md mr-2 text-slate-100 placeholder:text-slate-400"
        @input="updateValue"
      />
      <input
        v-model="trait.description"
        type="text"
        placeholder="Descripción (opcional)"
        class="flex-1 px-3 py-2 bg-navy-900/40 border border-emerald-800 rounded-md mr-2 text-slate-100 placeholder:text-slate-400"
        @input="updateValue"
      />
      <button
        @click="removeTrait(index)"
        type="button"
        class="btn-outline bg-rose-800/40 text-rose-200 hover:bg-rose-700/50 px-2 py-1 rounded"
        aria-label="Eliminar rasgo"
      >
        ×
      </button>
    </div>

    <button
      @click="addTrait"
      type="button"
      class="btn-gold"
    >
      + Agregar
    </button>
  </div>
</template>

<script setup lang="ts">
// no imports needed

interface Trait {
  name: string
  description?: string
}

// Acepta modelValue opcional y por defecto usa un array vacío para evitar undefined
const props = withDefaults(defineProps<{ modelValue?: Trait[] }>(), {
  modelValue: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: Trait[]]
}>()

function addTrait() {
  const base = props.modelValue ?? []
  const newTraits = [...base, { name: '', description: '' }]
  emit('update:modelValue', newTraits)
}

function removeTrait(index: number) {
  const base = props.modelValue ?? []
  const newTraits = base.filter((_, i) => i !== index)
  emit('update:modelValue', newTraits)
}

function updateValue() {
  // Force reactivity update
  const base = props.modelValue ?? []
  emit('update:modelValue', [...base])
}
</script>
