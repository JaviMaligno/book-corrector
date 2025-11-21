import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api, updateProject } from '../lib/api'
import { useState } from 'react'

type ProjectDetail = {
  id: string
  name: string
  lang_variant: string | null
  documents: { id: string; name: string; status: string }[]
  runs: { id: string; status: string; created_at: string }[]
}

export default function ProjectDetail(){
  const { projectId = '' } = useParams()
  const nav = useNavigate()
  const qc = useQueryClient()
  const { data } = useQuery({ queryKey: ['project', projectId], queryFn: async () => (await api.get<ProjectDetail>(`/projects/${projectId}`)).data })
  const [files, setFiles] = useState<FileList | null>(null)
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(false)
  const [editName, setEditName] = useState('')
  const [editVariant, setEditVariant] = useState('es-ES')
  const [editError, setEditError] = useState('')

  const upload = useMutation({
    mutationFn: async () => {
      if (!files || files.length === 0) return
      const form = new FormData()
      Array.from(files).forEach(f => form.append('files', f))
      await api.post(`/projects/${projectId}/documents/upload`, form)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', projectId] })
      setFiles(null)
    }
  })

  const update = useMutation({
    mutationFn: async () => {
      if (!editName.trim()) {
        throw new Error('El nombre del proyecto es requerido')
      }
      return await updateProject(projectId, {
        name: editName.trim(),
        lang_variant: editVariant
      })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['project', projectId] })
      setShowEditModal(false)
      setEditError('')
    },
    onError: (error: any) => {
      setEditError(error?.response?.data?.detail || error.message || 'Error al actualizar proyecto')
    }
  })

  const handleEditClick = () => {
    if (data) {
      setEditName(data.name)
      setEditVariant(data.lang_variant || 'es-ES')
      setEditError('')
      setShowEditModal(true)
    }
  }

  const handleUpdateClick = () => {
    setEditError('')
    update.mutate()
  }

  const run = useMutation({
    mutationFn: async () => {
      const docIds = selectedDocs.length > 0 ? selectedDocs : data?.documents?.map(d => d.id) || []
      const response = await api.post(`/runs`, {
        project_id: projectId,
        document_ids: docIds,
        use_ai: true
      })
      return response.data as { run_id: string }
    },
    onSuccess: (r: any) => {
      nav(`/runs/${r.run_id}`)
      setSelectedDocs([])
    },
    onError: (error: any) => {
      console.error('Error creating run:', error)
      alert(error.response?.data?.detail || 'Error al iniciar corrección')
    }
  })

  return (
    <div className="space-y-6">
      {/* Project Info Section */}
      <section className="card p-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-base font-medium">Proyecto</h2>
            <div className="text-sm text-gray-600 mt-1">{data?.name}</div>
            <div className="text-xs text-gray-500 mt-1">
              {data?.lang_variant || 'es-ES'}
            </div>
          </div>
          <button
            className="btn-secondary text-sm"
            onClick={handleEditClick}
          >
            Editar
          </button>
        </div>
      </section>

      {/* Edit Project Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-semibold mb-4">Editar proyecto</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre del proyecto *
                </label>
                <input
                  type="text"
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={editName}
                  onChange={e => setEditName(e.target.value)}
                  placeholder="Nombre del proyecto"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Variante de idioma
                </label>
                <select
                  className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={editVariant}
                  onChange={e => setEditVariant(e.target.value)}
                >
                  <option value="es-ES">Español (España)</option>
                  <option value="es-MX">Español (México)</option>
                </select>
              </div>

              {editError && (
                <div className="text-red-600 text-sm">
                  {editError}
                </div>
              )}

              <div className="flex gap-3 justify-end">
                <button
                  className="btn-secondary"
                  onClick={() => {
                    setShowEditModal(false)
                    setEditError('')
                  }}
                  disabled={update.isPending}
                >
                  Cancelar
                </button>
                <button
                  className="btn-primary"
                  onClick={handleUpdateClick}
                  disabled={update.isPending || !editName.trim()}
                >
                  {update.isPending ? 'Guardando...' : 'Guardar cambios'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <section className="card p-4">
        <h3 className="text-base font-medium mb-2">Subir documentos</h3>
        <input type="file" multiple accept=".docx,.txt" onChange={e=>setFiles(e.target.files)} />
        <button className="btn-primary mt-2" onClick={()=>upload.mutate()} disabled={upload.isPending || !files?.length}>Subir</button>
      </section>

      <section className="card p-4">
        <h3 className="text-base font-medium mb-2">Documentos</h3>
        {!data?.documents?.length && <div className="text-gray-500">Aún no hay documentos.</div>}
        <div className="space-y-2">
          {data?.documents?.map(d => (
            <label key={d.id} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
              <input
                type="checkbox"
                checked={selectedDocs.includes(d.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedDocs([...selectedDocs, d.id])
                  } else {
                    setSelectedDocs(selectedDocs.filter(id => id !== d.id))
                  }
                }}
                className="rounded"
              />
              <span className="text-sm">{d.name} <span className="text-gray-500">({d.status})</span></span>
            </label>
          ))}
        </div>
      </section>

      <section className="card p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-medium">Iniciar corrección</h3>
            <p className="text-xs text-gray-500 mt-1">
              {selectedDocs.length > 0
                ? `Se corregirán ${selectedDocs.length} documento(s) seleccionado(s)`
                : 'Se corregirán todos los documentos'}
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={()=>run.mutate()}
            disabled={run.isPending || !data?.documents?.length}
          >
            {run.isPending ? 'Enviando...' : 'Iniciar corrección'}
          </button>
        </div>
      </section>

      <section className="card p-4">
        <h3 className="text-base font-medium mb-2">Ejecuciones</h3>
        {!data?.runs?.length && <div className="text-gray-500">Aún no hay ejecuciones.</div>}
        <div className="space-y-2">
          {data?.runs?.map(r => (
            <Link
              key={r.id}
              to={`/runs/${r.id}`}
              className="block border rounded p-3 hover:bg-gray-50"
            >
              <div className="text-sm">
                <span className="font-medium">{r.id.slice(0,8)}</span> •
                <span className="ml-1">{r.status}</span> •
                <span className="ml-1 text-gray-500">{new Date(r.created_at).toLocaleString()}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

