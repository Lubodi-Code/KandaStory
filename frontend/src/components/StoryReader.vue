<template>
  <div class="flex flex-col gap-4">
    <!-- HEADER: progreso + acciones rápidas (sticky) -->
    <div class="sticky top-0 z-20">
      <div class="backdrop-blur-xl bg-neutral-900/70 border-b border-white/10 px-4 md:px-6 py-3">
        <div class="max-w-6xl mx-auto flex items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <!-- Indicador de progreso -->
            <div class="relative h-2 w-44 bg-white/10 rounded-full overflow-hidden">
              <div
                class="h-full bg-gold-400 transition-all duration-500"
                :style="{ width: progress + '%' }"
              />
            </div>
            <div class="text-xs text-zinc-300">
              Cap. <span class="font-semibold text-white">{{ Math.min(visibleChapter, chaptersNormalized.length) }}</span>
              / {{ chaptersNormalized.length }}
              <span class="opacity-60 ml-2">({{ progress }}%)</span>
            </div>
          </div>

          <!-- Timer compacto (si aplica) -->
          <div v-if="showTimer" class="shrink-0">
            <div class="rounded-lg bg-navy-900/40 border border-emerald-800 px-3 py-1.5 text-emerald-100 text-sm">
              ⏱️ Termina en <span class="font-semibold">{{ mmss(remainingSeconds) }}</span>
              • Listos {{ readyCount }}/{{ totalPlayers }}
            </div>
          </div>

          <!-- Acciones rápidas -->
          <div class="flex items-center gap-2">
            <button class="btn-ghost" @click="scrollTo(1)" title="Ir al inicio">Inicio</button>
            <button class="btn-gold" @click="scrollTo(currentChapter)" title="Ir al capítulo actual">Ir al actual</button>
          </div>
        </div>
      </div>
    </div>

  <!-- MOBILE: Índice plegable + export -->
  <details class="md:hidden bg-navy-900/50 text-zinc-100 rounded-2xl p-3 mx-2 border border-emerald-800">
      <summary class="list-none flex items-center justify-between cursor-pointer select-none">
        <span class="font-semibold">Índice de capítulos</span>
        <span class="text-sm opacity-80">ver ▾</span>
      </summary>

      <div class="mt-3">
        <ul class="divide-y divide-white/10 font-sans">
          <li v-for="ch in chaptersNormalized" :key="ch.chapter_number">
            <button
              class="w-full text-left py-2 transition"
              :class="visibleChapter === ch.chapter_number ? 'text-emerald-300 font-semibold' : 'text-zinc-300 hover:text-white'"
              @click="scrollTo(ch.chapter_number)"
            >
              Capítulo {{ ch.chapter_number }}
            </button>
          </li>
        </ul>

        <div class="mt-3 grid grid-cols-2 gap-2">
          <button class="btn-gold w-full" @click="scrollTo(currentChapter)">Ir al actual</button>
          <button class="btn-outline w-full" @click="scrollTo(chaptersNormalized.length)">Ir al final</button>
        </div>

        <div v-if="finished" class="mt-4 border-t border-white/10 pt-3">
          <h4 class="text-sm font-semibold mb-2">Exportar</h4>
          <div class="grid grid-cols-2 gap-2">
            <a class="btn-gold text-center" :href="`/api/games/${gameId}/export.txt`" target="_blank">.txt</a>
            <a class="btn-gold text-center" :href="`/api/games/${gameId}/export.pdf`" target="_blank">.pdf</a>
          </div>
        </div>
      </div>
    </details>

    <!-- DESKTOP: layout 2 columnas -->
    <div class="grid grid-cols-12 gap-6 px-2 md:px-4">
      <!-- Sidebar (solo ≥md) -->
      <aside class="hidden md:block md:col-span-4 lg:col-span-3 xl:col-span-2 sticky top-24 self-start">
        <div class="sidebar-panel rounded-2xl p-3 shadow">
          <h3 class="text-sm font-semibold mb-2 text-emerald-200/90">Capítulos</h3>

          <ul class="sidebar-list space-y-1 max-h-[60vh] overflow-auto pr-1">
            <li v-for="ch in chaptersNormalized" :key="ch.chapter_number">
              <button
                :aria-current="visibleChapter === ch.chapter_number ? 'true' : 'false'"
                :class="[
                  'w-full text-left px-3 py-2 rounded-xl transition group',
                  visibleChapter === ch.chapter_number
                    ? 'bg-emerald-600/20 text-emerald-100 ring-1 ring-emerald-500/40'
                    : 'hover:bg-white/5 text-emerald-200'
                ]"
                @click="scrollTo(ch.chapter_number)"
              >
                <span class="inline-flex items-center gap-2">
                  <span class="inline-block h-2 w-2 rounded-full"
                        :class="visibleChapter === ch.chapter_number ? 'bg-emerald-400' : 'bg-emerald-700/50 group-hover:bg-emerald-500/70'"/>
                  Capítulo {{ ch.chapter_number }}
                </span>
              </button>
            </li>
          </ul>

          <div class="mt-3 grid grid-cols-2 gap-2">
            <button class="btn-gold w-full" @click="scrollTo(currentChapter)">Ir al actual</button>
            <button class="btn-outline w-full" @click="scrollTo(1)">Inicio</button>
          </div>

          <div v-if="finished" class="mt-4 border-t border-white/10 pt-3">
            <h4 class="text-sm font-semibold mb-2 text-emerald-200/90">Exportar</h4>
            <div class="flex flex-col gap-2">
              <a class="btn text-center" :href="`/api/games/${gameId}/export.txt`" target="_blank">Descargar .txt</a>
              <a class="btn text-center" :href="`/api/games/${gameId}/export.pdf`" target="_blank">Descargar .pdf</a>
            </div>
          </div>
        </div>
      </aside>

      <!-- Reader -->
      <main class="col-span-12 md:col-span-8 lg:col-span-9 xl:col-span-10">
        <!-- Capítulos -->
        <article
          v-for="ch in chaptersNormalized"
          :key="ch.chapter_number"
          :id="chapterId(ch.chapter_number)"
          class="prose dark:prose-invert prose-zinc max-w-prose md:max-w-3xl lg:max-w-4xl !prose-headings:scroll-mt-24 mb-10 md:mb-12 px-1 md:px-2"
          ref="chapterRefs"
        >
          <header class="flex items-center justify-between gap-3 mb-3">
            <h2 class="!mb-0 text-2xl md:text-3xl font-bold text-zinc-100">
              Capítulo {{ ch.chapter_number }}
            </h2>
            <span
              class="text-[11px] uppercase tracking-wide px-2 py-1 rounded-md border border-white/10 text-zinc-300 bg-white/5"
              :class="visibleChapter === ch.chapter_number ? 'ring-1 ring-emerald-500/30 text-emerald-200' : ''"
            >
              {{ visibleChapter === ch.chapter_number ? 'Leyendo' : '—' }}
            </span>
          </header>

          <div class="reader-card reader-card-navy">
           <div class="reader-text not-prose whitespace-pre-line" style="--reader-text-color:#fff;">
  {{ ch.content }}
</div>

          </div>
        </article>

        <!-- Sin capítulos -->
        <div v-if="chaptersNormalized.length === 0" class="text-center py-12 text-zinc-400">
          <div class="text-4xl mb-2">📖</div>
          <p>Esperando el primer capítulo…</p>
        </div>

        <!-- Panel de acciones (solo durante action_phase) -->
        <div v-if="allowActions && !finished && showTimer" class="md:mt-6">
          <div class="action-card rounded-2xl p-4 bg-navy-900/40 border border-emerald-800">
            <h3 class="text-lg font-semibold mb-2 text-emerald-200">💭 Proponer acción</h3>
            <textarea
              v-model="actionText"
              rows="3"
              placeholder="Acción + objetivo + posible consecuencia…"
              class="w-full rounded-xl border border-emerald-800 px-3 py-2 bg-navy-900/40 text-zinc-100 placeholder:text-zinc-500 resize-y focus:ring-2 focus:ring-gold-400 focus:border-emerald-500 outline-none"
            ></textarea>
            <div class="mt-3 grid grid-cols-2 gap-2">
              <button class="btn-gold" :disabled="sending || !actionText.trim() || submittedAction" @click="submitAction">
                {{ submittedAction ? '✅ Acción enviada' : (sending ? '⏳ Enviando…' : '🚀 Enviar acción') }}
              </button>
              <button class="btn-outline" :disabled="ready || buttonDisabled" @click="markReady">
                {{ ready ? '✅ Listo' : '👍 Estoy listo' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Estado final -->
        <div v-if="finished" class="mt-6">
          <div class="bg-emerald-900/30 border border-emerald-800 rounded-2xl p-6 text-center text-emerald-100">
            <div class="text-4xl mb-2">🎉</div>
            <h3 class="text-xl font-bold mb-1">¡Historia completada!</h3>
            <p class="opacity-90">Exporta la historia desde el menú “Capítulos”.</p>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, nextTick, watch, computed } from 'vue'

interface Chapter {
  chapter_number: number
  content: string
}

const props = defineProps<{
  gameId: string
  chapters: Array<Chapter | string>
  currentChapter: number
  finished: boolean
  allowActions: boolean
  showTimer: boolean
  remainingSeconds: number
  readyCount: number
  totalPlayers: number
  ready: boolean
  buttonDisabled?: boolean
  submittedAction?: boolean
}>()

const emit = defineEmits<{
  'submit:action': [text: string]
  'click:ready': []
}>()

const actionText = ref('')
const sending = ref(false)
const chapterRefs = ref<HTMLElement[]>([])
const visibleChapter = ref<number>(props.currentChapter)

const chapterId = (n: number) => `chapter-${n}`

// Normaliza capítulos para soportar string[] o { chapter_number, content }[]
const chaptersNormalized = computed<Chapter[]>(() => {
  return props.chapters.map((ch, idx) =>
    typeof ch === 'string'
      ? { chapter_number: idx + 1, content: ch }
      : ch
  )
})

const progress = computed(() => {
  const total = chaptersNormalized.value.length
  if (!total) return 0
  const idx = Math.max(1, Math.min(visibleChapter.value, total))
  return Math.round((idx / total) * 100)
})

const scrollTo = async (n: number) => {
  await nextTick()
  // Clamp requested chapter to valid range
  const total = chaptersNormalized.value.length
  let target = Math.max(1, Math.min(n || 1, total))

  const el = document.getElementById(chapterId(target))
  if (!el) return

  // Calcular offset por la cabecera sticky (buscar elemento con la clase del header)
  const header = document.querySelector('.backdrop-blur-xl') as HTMLElement | null
  const headerHeight = header ? Math.round(header.getBoundingClientRect().height) : 96
  const extraGap = 28 // un pequeño margen extra visual (aumentado para mostrar el capítulo un poco más arriba)

  const y = window.scrollY + el.getBoundingClientRect().top - headerHeight - extraGap
  window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' })
  // Actualizar estado visible inmediatamente para que el progreso cambie
  visibleChapter.value = target
}

const mmss = (s: number) => {
  const m = Math.floor(s / 60)
  const r = s % 60
  return `${m.toString().padStart(2,'0')}:${r.toString().padStart(2,'0')}`
}

// Intersection Observer para scrollspy
let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id.replace('chapter-','')
        const num = Number(id)
        if (!isNaN(num)) visibleChapter.value = num
      }
    })
  }, {
    rootMargin: '-20% 0px -60% 0px',
    threshold: 0.1
  })

  const chapterElements = Array.from(document.querySelectorAll('[id^="chapter-"]')) as HTMLElement[]
  chapterElements.forEach(el => observer?.observe(el))
})

onBeforeUnmount(() => {
  observer?.disconnect()
})

// Reobservar cuando cambien los capítulos
watch(() => props.chapters.length, async () => {
  await nextTick()
  if (observer) {
    observer.disconnect()
    const chapterElements = Array.from(document.querySelectorAll('[id^="chapter-"]')) as HTMLElement[]
    chapterElements.forEach(el => observer?.observe(el))
  }
})

// Scroll automático al capítulo actual cuando cambie
watch(() => props.currentChapter, async (newChapter) => {
  await nextTick()
  if (Math.abs(visibleChapter.value - newChapter) > 1) {
    scrollTo(newChapter)
  }
})

// Si el juego se marca como terminado, asegúrate de mostrar y saltar al último capítulo
watch(() => props.finished, async (f) => {
  if (!f) return
  await nextTick()
  const last = chaptersNormalized.value.length
  if (last > 0) {
    // Forzar visibleChapter al último y hacer scroll
    visibleChapter.value = last
    scrollTo(last)
  }
})

async function submitAction() {
  if (!actionText.value.trim() || sending.value) return
  sending.value = true
  try {
    emit('submit:action', actionText.value.trim())
    actionText.value = ''
  } finally {
    sending.value = false
  }
}

function markReady() {
  emit('click:ready')
}
</script>

<style scoped>
/* —— Botones ————————————————————————————————————————————— */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  transition: transform .08s ease, box-shadow .2s ease, filter .2s ease;
  box-shadow: 0 8px 20px rgba(16,185,129,0.25);
}
.btn:hover:not(:disabled) {
  filter: brightness(1.05);
  box-shadow: 0 10px 24px rgba(16,185,129,0.35);
}
.btn:active:not(:disabled) { transform: translateY(1px); }
.btn:disabled { background: #374151; color: #a3a3a3; cursor: not-allowed; box-shadow: none; }

.btn-outline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.75rem;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  border: 1px solid rgba(16,185,129,0.45);
  color: #d1fae5;
  background: transparent;
  transition: all .2s ease;
}
.btn-outline:hover:not(:disabled) { background: rgba(16,185,129,0.10); }
.btn-outline:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-ghost {
  padding: .35rem .75rem;
  border-radius: .65rem;
  font-weight: 600;
  color: #c4cbd5;
  background: transparent;
  border: 1px solid transparent;
  transition: all .2s ease;
}
.btn-ghost:hover { background: rgba(255,255,255,.05); border-color: rgba(255,255,255,.08); }

/* —— Reader Cards ———————————————————————————————————— */
.reader-card {
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.65), rgba(15, 23, 42, 0.45));
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 1.25rem;
  padding: 1.25rem;
  box-shadow: 0 20px 60px rgba(0,0,0,.25);
}

/* Tipografía de lectura mejorada */
.reader-text {
  font-family: 'Merriweather', ui-serif, Georgia, Cambria, "Times New Roman", Times, serif;
  font-size: 1.0625rem;
  line-height: 1.9;
  letter-spacing: 0.002em;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  max-width: 72ch;
  /* Color por defecto: esmeralda claro (mejor legibilidad sobre fondo oscuro).
    Se puede sobrescribir con la variable CSS --reader-text-color, una clase helper
    (.reader-text--emerald / .reader-text--white) o con una clase Tailwind en el template. */
  color: var(--reader-text-color, rgb(187 247 208));
  hyphens: auto;
  overflow-wrap: anywhere;
}
/* Helper classes para alternar rápido el color del texto del lector */
.reader-text--emerald { --reader-text-color: rgb(187 247 208); }
.reader-text--emerald-300 { --reader-text-color: rgb(134 239 172); }
.reader-text--white { --reader-text-color: #ffffff; }
@media (min-width: 768px) {
  .reader-text { font-size: 1.125rem; line-height: 1.9; }
}
.reader-text p { margin: 0 0 1em; }
.reader-text p + p { text-indent: 1.25em; }
.reader-text h2, .reader-text h3 { text-indent: 0; }

/* Prose headers */
.prose h2 { color: rgb(244 244 245); font-family: 'Merriweather', serif; }
.prose h2 { scroll-margin-top: 8rem; }

/* —— Sidebar ———————————————————————————————————————— */
.sidebar-panel {
  background: linear-gradient(180deg, rgba(0,0,0,.8), rgba(8,8,8,.72));
  border: 1px solid rgba(255,255,255,0.05);
  color: #e5fff6;
}
.sidebar-list {
  font-family: 'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
  color: #d1fae5;
}
.sidebar-list::-webkit-scrollbar { width: 8px; }
.sidebar-list::-webkit-scrollbar-thumb { background-color: rgba(16,185,129,0.25); border-radius: 9999px; }

/* —— Action Card ————————————————————————————————————— */
.action-card {
  background: rgba(17, 24, 39, .6);
  border: 1px solid rgba(255,255,255,.06);
  backdrop-filter: blur(8px);
}
</style>
