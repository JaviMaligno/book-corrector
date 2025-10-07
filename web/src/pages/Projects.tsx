import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

type Project = {
  id: string
  name: string
  variant?: string
  mode?: string
  created_at: string
}

export default function Projects(){
  const qc = useQueryClient()
  const { isAuthenticated } = useAuth()

  // Only fetch projects if user is authenticated
  const { data, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => (await api.get<Project[]>('/projects')).data,
    enabled: isAuthenticated,
    retry: (failureCount, error: any) => {
      // No retry on 401/403 errors (authentication issues)
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        return false
      }
      return failureCount < 3
    }
  })

  const [name, setName] = useState('Proyecto de ejemplo')
  const [variant, setVariant] = useState('es-ES')
  const [mode, setMode] = useState('rapido')

  const create = useMutation({
    mutationFn: async () => (await api.post<Project>('/projects', { name, variant, mode })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] })
  })

  // If not authenticated, show login/register prompt
  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto">
        <div className="card p-6 text-center">
          <h2 className="text-xl font-semibold mb-4">Bienvenido a Corrector</h2>
          <p className="text-gray-600 mb-6">
            Para crear y gestionar proyectos de corrección de texto, necesitas una cuenta.
          </p>
          <div className="space-y-3">
            <Link
              to="/login"
              className="btn-primary w-full block text-center"
            >
              Iniciar sesión
            </Link>
            <Link
              to="/register"
              className="btn-secondary w-full block text-center"
            >
              Crear cuenta
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <section className="card p-4">
        <h2 className="text-base font-medium mb-3">Nuevo proyecto</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input className="border rounded px-3 py-2" value={name} onChange={e=>setName(e.target.value)} placeholder="Nombre" />
          <select className="border rounded px-3 py-2" value={variant} onChange={e=>setVariant(e.target.value)}>
            <option>es-ES</option>
            <option>es-MX</option>
          </select>
          <select className="border rounded px-3 py-2" value={mode} onChange={e=>setMode(e.target.value)}>
            <option value="rapido">Rápido</option>
            <option value="profesional">Profesional</option>
          </select>
          <button className="btn-primary" onClick={()=>create.mutate()} disabled={create.isPending}>Crear</button>
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-base font-medium mb-3">Proyectos</h2>

        {isLoading && (
          <div className="text-gray-500">Cargando proyectos...</div>
        )}

        {error && (
          <div className="text-red-500 mb-4">
            Error al cargar proyectos: {error instanceof Error ? error.message : 'Error desconocido'}
          </div>
        )}

        {!isLoading && !error && !data?.length && (
          <div className="text-gray-500">Aún no hay proyectos.</div>
        )}

        {!isLoading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data?.map(p => (
              <Link to={`/projects/${p.id}`} key={p.id} className="border rounded p-3 hover:bg-gray-50">
                <div className="text-brand-ink font-medium">{p.name}</div>
                <div className="text-sm text-gray-500">{p.variant} • {p.mode} • {new Date(p.created_at).toLocaleString()}</div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

