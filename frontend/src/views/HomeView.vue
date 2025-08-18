<template>
  <div class="max-w-2xl mx-auto relative" style="min-height: calc(100vh - 6rem);">
    <!-- Background image + overlay -->
  <!-- Decorative image removed: keep solid/directional gradient overlay only -->

  <h1 class="text-3xl font-bold mb-8 text-center text-gold-400">Bienvenido a KandaStory</h1>
    
    <div class="card-navy p-6 rounded-lg shadow-xl border card-accent">
      <h2 class="text-xl font-semibold mb-4 text-emerald-200">¡Crea tu primera aventura!</h2>
      <p class="text-slate-300 mb-4">
        En KandaStory puedes crear personajes únicos con IA, unirte a salas de aventuras 
        y vivir historias generadas colaborativamente.
      </p>
      
      <div class="space-y-4">
    <div v-if="!authStore.isAuthenticated" class="text-center">
          <router-link 
            to="/register" 
      class="btn-gold mr-4"
          >
            Comenzar
        <!-- Adventure-style colorful background (radials + subtle SVG pattern) -->
        <div class="absolute inset-0 -z-10 adventure-bg" aria-hidden="true"></div>
        <div class="absolute inset-0 -z-5 bg-gradient-to-b from-navy-900/40 to-black/40"></div>
            class="btn-outline"
          >
            Ya tengo cuenta
          </router-link>
        </div>
        
        <div v-else class="text-center">
          <router-link 
            to="/characters" 
            class="btn mr-4"
          >
            Mis Personajes
          </router-link>
          <router-link 
            to="/rooms" 
            class="btn-outline"
          >
            Salas de Aventura
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.adventure-bg{
  /* layered colorful radials to give a map/adventure vibe */
  background-image:
    radial-gradient(600px 300px at 10% 20%, rgba(16,185,129,0.06), transparent 20%),
    radial-gradient(500px 220px at 85% 80%, rgba(249,115,22,0.06), transparent 18%),
    radial-gradient(400px 180px at 60% 15%, rgba(34,197,94,0.04), transparent 16%),
    linear-gradient(180deg, rgba(2,6,23,0.95), rgba(6,8,15,0.9));
  background-size: cover;
  background-repeat: no-repeat;
  background-attachment: fixed;
  /* subtle tiled SVG pattern (maps / icons style) */
  mask-image: linear-gradient(rgba(0,0,0,0.95), rgba(0,0,0,0.95));
  position: relative;
}

.adventure-bg::before{
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 240 240'><g fill='none' stroke='%23000000' stroke-opacity='0.06' stroke-width='2'><path d='M20 30c40-10 60 10 80 0s40-20 70-10'/><circle cx='40' cy='180' r='6'/><path d='M120 60 l30 0'/><path d='M200 20 l-12 18'/></g></svg>");
  opacity: 0.12;
  mix-blend-mode: overlay;
  pointer-events: none;
}

.adventure-bg::after{
  /* very subtle noise to add texture */
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><filter id='n'><feTurbulence baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.03'/></svg>");
  mix-blend-mode: overlay;
  pointer-events:none;
}

/* responsive tuning to keep area readable */
@media (max-width: 768px){
  .adventure-bg{ background-attachment: scroll; }
  .adventure-bg::before{ opacity: 0.08 }
}
</style>
