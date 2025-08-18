import axios from 'axios'

export async function pingBackend(payload: Record<string, any> = {}) {
  try {
    const res = await axios.post(`/api/connect`, payload)
    console.log('[connectivity] backend response:', res.data)
    return res.data
  } catch (err) {
    console.warn('[connectivity] error calling backend:', err)
    throw err
  }
}
