import axios from 'axios'
import { API_URL } from './env'

export const api = axios.create({ baseURL: API_URL, timeout: 20_000 })

export async function ping(): Promise<{ ok: boolean }> {
  try {
    await api.get('/health')
    return { ok: true }
  } catch {
    return { ok: false }
  }
}

