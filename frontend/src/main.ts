import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import axios from 'axios'

import App from './App.vue'
import router from './router'

// Remove axios baseURL to use Vite proxy
// axios.defaults.baseURL = 'http://127.0.0.1:8000'

const app = createApp(App)

// Load Vue Devtools only in development
if (import.meta.env.DEV) {
	// Dynamic import so production bundles don't include devtools.
	// @ts-ignore - dev-only package
	import('@vue/devtools')
		.then((devtools) => {
			try {
				// Some versions expose `connect` or `install`.
				if (devtools && typeof (devtools as any).connect === 'function') {
					;(devtools as any).connect()
				} else if (devtools && typeof (devtools as any).install === 'function') {
					;(devtools as any).install()
				}
			} catch (e) {
				// ignore devtools errors
			}
		})
		.catch(() => {
			// ignore import failure in environments where package isn't installed
		})
}

app.use(createPinia())
app.use(router)

// In development, ping the backend once the app mounts to validate connectivity
if (import.meta.env.DEV) {
	import('./lib/connectivity')
		.then((mod) => {
			// small payload with timestamp
			mod.pingBackend({ ts: new Date().toISOString() }).catch(() => {})
		})
		.catch(() => {})
}

app.mount('#app')
