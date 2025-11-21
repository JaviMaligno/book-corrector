import axios from 'axios'
import { API_URL } from './env'
import type { Project } from './types'

export const api = axios.create({ baseURL: API_URL, timeout: 20_000 })

export async function ping(): Promise<{ ok: boolean }> {
  try {
    await api.get('/health')
    return { ok: true }
  } catch {
    return { ok: false }
  }
}

// Project API helpers
export async function createProject(
  name: string,
  langVariant?: string
): Promise<Project> {
  const response = await api.post<Project>('/projects', {
    name,
    lang_variant: langVariant || null
  })
  return response.data
}

export async function updateProject(
  projectId: string,
  updates: { name?: string; lang_variant?: string }
): Promise<Project> {
  const response = await api.patch<Project>(`/projects/${projectId}`, updates)
  return response.data
}

export async function deleteProject(projectId: string): Promise<void> {
  await api.delete(`/projects/${projectId}`)
}

