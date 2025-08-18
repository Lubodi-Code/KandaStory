<template>
  <!-- Monta en <body> para evitar z-index raros -->
  <Teleport to="body">
    <!-- Fade del backdrop -->
    <Transition enter-active-class="transition ease-out duration-200"
                enter-from-class="opacity-0"
                enter-to-class="opacity-100"
                leave-active-class="transition ease-in duration-150"
                leave-from-class="opacity-100"
                leave-to-class="opacity-0">
      <div class="fixed inset-0 z-50" @keydown.esc.stop.prevent="$emit('close')" ref="root">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('close')" />
        <!-- Contenedor centrado (clic fuera cierra) -->
        <div class="relative min-h-full flex items-center justify-center p-4" @click.self="$emit('close')">
          <!-- Pop del modal -->
          <Transition enter-active-class="transition ease-out duration-200"
                      enter-from-class="opacity-0 translate-y-2 scale-[.98]"
                      enter-to-class="opacity-100 translate-y-0 scale-100"
                      leave-active-class="transition ease-in duration-150"
                      leave-from-class="opacity-100 translate-y-0 scale-100"
                      leave-to-class="opacity-0 translate-y-2 scale-[.98]">
            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="chapter-actions-title"
              class="relative w-full max-w-2xl rounded-2xl bg-navy-900/80 border border-emerald-700 ring-1 ring-white/5 shadow-2xl"
              @click.stop
            >
              <!-- Header -->
              <header class="flex items-center justify-between px-5 py-4 border-b border-emerald-800/80">
                <h3 id="chapter-actions-title" class="text-lg font-semibold text-gold-300">
                  Acciones del capítulo
                  <span v-if="chapter !== null" class="ml-2 text-sm text-slate-400">#{{ chapter }}</span>
                </h3>
                <button
                  ref="closeBtn"
                  class="rounded-lg px-2.5 py-1.5 text-slate-300 hover:text-emerald-200 hover:bg-gray-800/70 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  @click="$emit('close')"
                  aria-label="Cerrar"
                >
                  ✕
                </button>
              </header>

              <!-- Sutile bar de acento -->
              <div class="h-1 bg-gradient-to-r from-gold-400/50 via-emerald-400/50 to-navy-600/40"></div>

              <!-- Contenido -->
              <section class="max-h-[60vh] overflow-auto p-5 text-zinc-100">
                <div v-if="!actions || actions.length === 0" class="text-slate-400 italic">
                  No hay acciones pendientes.
                </div>

                <ul v-else class="space-y-3">
                  <li
                    v-for="(action, i) in actions"
                    :key="action.id ?? i"
                    class="rounded-xl border border-emerald-800/70 bg-navy-900/40 p-4 hover:bg-navy-900/50 transition"
                  >
                      <div class="mb-2 font-medium text-emerald-200">
                      {{ action.title ?? 'Acción' }}
                    </div>

                    <p class="text-sm text-slate-200/90 whitespace-pre-wrap leading-relaxed">
                      {{ action.description ?? 'Sin descripción' }}
                    </p>

                    <div class="mt-3 flex flex-wrap gap-2">
                      <button class="btn-gold" @click="execute(action)">Ejecutar</button>

                      <button
                        v-if="action.secondary"
                        class="btn-outline"
                        @click="$emit('execute', action.secondary)"
                      >
                        {{ action.secondary.title ?? 'Acción secundaria' }}
                      </button>
                    </div>
                  </li>
                </ul>
              </section>

              <!-- Footer -->
              <footer class="flex justify-end gap-2 border-t border-emerald-800/80 px-5 py-4">
                <button class="btn-outline" @click="$emit('close')">Cerrar</button>
              </footer>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { defineProps, defineEmits, onMounted, ref } from 'vue'

defineProps<{
  actions: Array<any>
  chapter: number | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'execute', action: any): void
}>()

function execute(action: any) {
  emit('execute', action)
}

const root = ref<HTMLElement | null>(null)
const closeBtn = ref<HTMLButtonElement | null>(null)

onMounted(() => {
  // foco inicial para accesibilidad
  closeBtn.value?.focus()
})
</script>

<style scoped>
/* Reutiliza tu estética de botones: oro principal, esmeralda secundario, fondo navy */
.btn-gold{
  display:inline-flex;align-items:center;justify-content:center;
  border-radius:.75rem;padding:.5rem 1rem;font-size:.875rem;font-weight:700;
  background:linear-gradient(135deg,#d4af37,#b8860b);color:#0b0b0b;
  transition:transform .08s, box-shadow .2s, filter .2s;
  box-shadow:0 8px 20px rgba(212,175,55,.14)
}
.btn-gold:hover{ filter:brightness(1.03); box-shadow:0 10px 24px rgba(212,175,55,.2) }
.btn-gold:active{ transform:translateY(1px) }
.btn-gold:disabled{ background:#2b2f37;color:#8b8b8b; box-shadow:none; cursor:not-allowed }

.btn-outline{
  display:inline-flex;align-items:center;justify-content:center;
  border-radius:.75rem;padding:.5rem 1rem;font-size:.875rem;font-weight:600;
  border:1px solid rgba(16,185,129,.28);color:#d1fae5;background:transparent;
  transition:all .2s
}
.btn-outline:hover{ background:rgba(16,185,129,.06) }
</style>
