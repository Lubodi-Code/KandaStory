import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  // Load env vars so we can use VITE_API_BASE_URL / VITE_WS_BASE_URL
  const env = loadEnv(mode, process.cwd(), '')
  const apiTarget = env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
  const wsTarget = env.VITE_WS_BASE_URL || 'ws://127.0.0.1:8000'

  // Attempt to enable Vue Devtools when running the dev server.
  // This uses a dynamic import so production builds are unaffected.
  if (mode === 'development') {
    import('@vue/devtools')
      .then((devtools) => {
        try {
          if (devtools && typeof devtools.connect === 'function') {
            devtools.connect()
          } else if (devtools && typeof devtools.install === 'function') {
            devtools.install()
          }
        } catch (e) {
          // ignore devtools runtime errors
        }
      })
      .catch(() => {
        // package not installed or cannot be loaded in this environment
      })
  }

  return {
    plugins: [vue()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/ws': {
          target: wsTarget,
          ws: true,
          changeOrigin: true,
        },
      },
    },
  }
})
