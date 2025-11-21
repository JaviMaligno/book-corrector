import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../lib/api'
import { useState } from 'react'

type Project = {
  id: string
  name: string
  documents: { id: string; name: string; status: string }[]
  runs: { id: string; status: string; created_at: string }[]
}

export default function ProjectDetail(){
  const { projectId = '' } = useParams()
  const nav = useNavigate()
  const qc = useQueryClient()
  const { data } = useQuery({ queryKey: ['project', projectId], queryFn: async () => (await api.get<Project>(`/projects/${projectId}`)).data })
  const [files, setFiles] = useState<FileList | null>(null)
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])

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
      <section className="card p-4">
        <h2 className="text-base font-medium">Proyecto</h2>
        <div className="text-sm text-gray-600">{data?.name}</div>
      </section>

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

