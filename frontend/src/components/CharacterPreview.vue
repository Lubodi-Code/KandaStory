<template>
  <div class="p-4 rounded-lg shadow-md card-navy border text-slate-100">
    <div class="flex items-center justify-between mb-3">
      <h3 class="font-semibold text-lg text-gold-400">{{ character.name }}</h3>
    </div>

    <div class="space-y-3 text-sm">
      <div>
        <div class="text-emerald-200 font-medium mb-1">Físico</div>
        <div class="flex flex-wrap">
          <span v-for="(t, i) in character.physical" :key="`phys-${i}`" class="inline-block bg-navy-800/40 text-emerald-200 px-2 py-0.5 rounded-full text-xs mr-2 mb-2">{{ t.name }}</span>
        </div>
      </div>

      <div>
        <div class="text-emerald-200 font-medium mb-1">Mental</div>
        <div class="flex flex-wrap">
          <span v-for="(t, i) in character.mental" :key="`ment-${i}`" class="inline-block bg-navy-800/40 text-emerald-200 px-2 py-0.5 rounded-full text-xs mr-2 mb-2">{{ t.name }}</span>
        </div>
      </div>

      <div>
        <div class="text-emerald-200 font-medium mb-1">Habilidades</div>
        <div class="flex flex-wrap">
          <span v-for="(t, i) in character.skills" :key="`skill-${i}`" class="inline-block bg-navy-800/40 text-emerald-200 px-2 py-0.5 rounded-full text-xs mr-2 mb-2">{{ t.name }}</span>
        </div>
      </div>

      <div>
        <div class="text-emerald-200 font-medium mb-1">Defectos</div>
        <div class="flex flex-wrap">
          <span v-for="(t, i) in character.flaws" :key="`flaw-${i}`" class="inline-block bg-navy-800/30 text-rose-200 px-2 py-0.5 rounded-full text-xs mr-2 mb-2">{{ t.name }}</span>
        </div>
      </div>

      <div v-if="character.background">
        <div class="text-emerald-200 font-medium mb-1">Historia</div>
        <div class="text-slate-300 text-sm leading-relaxed">{{ character.background }}</div>
      </div>

      <div v-if="character.beliefs">
        <div class="text-emerald-200 font-medium mb-1">Creencias</div>
        <div class="text-slate-300 text-sm leading-relaxed">{{ character.beliefs }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Trait {
  name: string
  description?: string
}

interface Character {
  name: string
  physical: Trait[]
  mental: Trait[]
  skills: Trait[]
  flaws: Trait[]
  background?: string
  beliefs?: string
}

defineProps<{
  character: Character
}>()
</script>
