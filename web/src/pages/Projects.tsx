import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, createProject } from '../lib/api'
import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import type { Project } from '../lib/types'

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

  // Modal state for creating projects
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [name, setName] = useState('')
  const [variant, setVariant] = useState('es-ES')
  const [createError, setCreateError] = useState('')

  const create = useMutation({
    mutationFn: async () => {
      if (!name.trim()) {
        throw new Error('El nombre del proyecto es requerido')
      }
      return await createProject(name.trim(), variant)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['projects'] })
      // Reset form and close modal
      setName('')
      setVariant('es-ES')
      setShowCreateModal(false)
      setCreateError('')
    },
    onError: (error: any) => {
      setCreateError(error?.response?.data?.detail || error.message || 'Error al crear proyecto')
    }
  })

  const handleCreateClick = () => {
    setCreateError('')
    create.mutate()
  }

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
      {/* Create Project Button */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Proyectos</h1>
        <button
          className="btn-primary"
          onClick={() => setShowCreateModal(true)}
        >
          + Crear proyecto
        </button>
      </div>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-semibold mb-4">Crear nuevo proyecto</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre del proyecto *
                </label>
                <input
                  type="text"
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Ej: Tesis 2024"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Variante de idioma
                </label>
                <select
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={variant}
                  onChange={e => setVariant(e.target.value)}
                >
                  <option value="es-ES">Español (España)</option>
                  <option value="es-MX">Español (México)</option>
                </select>
              </div>

              {createError && (
                <div className="text-red-600 text-sm">
                  {createError}
                </div>
              )}

              <div className="flex gap-3 justify-end">
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setShowCreateModal(false)
                    setName('')
                    setVariant('es-ES')
                    setCreateError('')
                  }}
                  disabled={create.isPending}
                >
                  Cancelar
                </button>
                <button
                  className="btn-primary"
                  onClick={handleCreateClick}
                  disabled={create.isPending || !name.trim()}
                >
                  {create.isPending ? 'Creando...' : 'Crear proyecto'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Projects List */}
      <section className="card p-4">
        {isLoading && (
          <div className="text-gray-500">Cargando proyectos...</div>
        )}

        {error && (
          <div className="text-red-500 mb-4">
            Error al cargar proyectos: {error instanceof Error ? error.message : 'Error desconocido'}
          </div>
        )}

        {!isLoading && !error && !data?.length && (
          <div className="text-gray-500 text-center py-8">
            Aún no hay proyectos. Haz clic en "Crear proyecto" para comenzar.
          </div>
        )}

        {!isLoading && !error && data && data.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.map(p => (
              <Link to={`/projects/${p.id}`} key={p.id} className="border rounded p-3 hover:bg-gray-50 transition-colors">
                <div className="text-brand-ink font-medium">{p.name}</div>
                <div className="text-sm text-gray-500">
                  {p.lang_variant || 'es-ES'} • {new Date(p.created_at).toLocaleString()}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

