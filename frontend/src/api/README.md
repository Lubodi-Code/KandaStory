# APIs del Frontend - KandaStory

Esta carpeta contiene todos los servicios de API organizados y tipados para el frontend.

## Estructura

```
src/
├── lib/
│   └── api.ts          # Instancia configurada de axios
└── api/
    ├── index.ts        # Exportaciones principales
    ├── ApiAuth.ts      # Autenticación y usuarios
    ├── ApiCharacter.ts # Personajes
    ├── ApiGame.ts      # Salas y juego
    ├── ApiWorld.ts     # Mundos
    └── examples.ts     # Ejemplos de uso
```

## Configuración

### Variables de entorno (.env)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

### Instancia de API (lib/api.ts)

- Configuración centralizada de axios
- Interceptors para autenticación automática
- Manejo de errores y redirección en caso de token expirado
- Base URL configurable por entorno

## Servicios Disponibles

### ApiAuth
- `login(credentials)` - Iniciar sesión
- `register(userData)` - Registrar usuario
- `verifyEmail(token)` - Verificar email
- `getCurrentUser()` - Obtener usuario actual
- `resendVerification(email)` - Reenviar verificación

### ApiCharacter
- `getUserCharacters()` - Obtener personajes del usuario
- `getCharacter(id)` - Obtener personaje por ID
- `createCharacter(data)` - Crear personaje
- `updateCharacter(id, data)` - Actualizar personaje
- `deleteCharacter(id)` - Eliminar personaje
- `getCharactersByWorld(worldId)` - Personajes por mundo

### ApiGame
- `getRooms()` - Obtener salas
- `getRoom(id)` - Obtener sala por ID
- `createRoom(data)` - Crear sala
- `joinRoom(id)` - Unirse a sala
- `leaveRoom(id)` - Salir de sala
- `selectCharacter(roomId, characterId)` - Seleccionar personaje
- `toggleReady(roomId)` - Cambiar estado listo
- `startGame(roomId)` - Iniciar juego
- `createWebSocket(roomId, token)` - Crear conexión WebSocket

### ApiWorld
- `getWorlds()` - Obtener mundos
- `getWorld(id)` - Obtener mundo por ID

## Uso en Componentes

### Importación
```typescript
import { apiAuth, apiCharacter, apiGame, apiWorld } from '@/api'
import type { Character, Room, World } from '@/api'
```

### En stores de Pinia
```typescript
import { defineStore } from 'pinia'
import { apiAuth, type User } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // ... estado reactivo
  
  const login = async (email: string, password: string) => {
    const response = await apiAuth.login({ username: email, password })
    // ... manejo del estado
  }
  
  return { login, /* ... */ }
})
```

### En componentes Vue
```typescript
<script setup lang="ts">
import { apiCharacter, type Character } from '@/api'

const characters = ref<Character[]>([])

const fetchCharacters = async () => {
  try {
    characters.value = await apiCharacter.getUserCharacters()
  } catch (error) {
    console.error('Error:', error)
  }
}

onMounted(fetchCharacters)
</script>
```

## Ventajas

1. **Tipado fuerte**: Todos los tipos están definidos con TypeScript
2. **Autenticación automática**: Los tokens se manejan automáticamente
3. **Manejo de errores**: Interceptors para errores globales
4. **Configuración centralizada**: URLs y timeouts en un solo lugar
5. **Fácil testing**: Servicios aislados y mockeable
6. **Reutilización**: Mismos servicios en stores y componentes
7. **WebSocket integrado**: Conexiones WebSocket configuradas

## WebSocket

El servicio `ApiGame` incluye un método para crear conexiones WebSocket:

```typescript
const ws = apiGame.createWebSocket(roomId, token)

ws.onopen = () => console.log('Conectado')
ws.onmessage = (event) => {
  const message = JSON.parse(event.data)
  // Manejar mensaje
}
ws.onclose = () => console.log('Desconectado')
```

## Manejo de errores

Los interceptors manejan automáticamente:
- Tokens expirados (redirige al login)
- Errores de red
- Respuestas de error del servidor

Para manejar errores específicos en componentes:

```typescript
try {
  await apiCharacter.createCharacter(data)
} catch (error: any) {
  const message = error.response?.data?.detail || 'Error desconocido'
  // Mostrar mensaje de error
}
```
