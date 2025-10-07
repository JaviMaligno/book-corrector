import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams, useNavigate } from 'react-router-dom'
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

  const upload = useMutation({
    mutationFn: async () => {
      if (!files || files.length === 0) return
      const form = new FormData()
      Array.from(files).forEach(f => form.append('files', f))
      await api.post(`/projects/${projectId}/documents/upload`, form)
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['project', projectId] })
  })

  const run = useMutation({
    mutationFn: async () => (await api.post(`/projects/${projectId}/runs`, new FormData())).data as { id: string },
    onSuccess: (r: any) => nav(`/runs/${r.id}`)
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
        <ul className="list-disc pl-6">
          {data?.documents?.map(d => (
            <li key={d.id} className="text-sm">{d.name} <span className="text-gray-500">({d.status})</span></li>
          ))}
        </ul>
      </section>

      <section className="card p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-medium">Ejecuciones</h3>
          <button className="btn-primary" onClick={()=>run.mutate()} disabled={run.isPending || !data?.documents?.length}>Corregir</button>
        </div>
        {!data?.runs?.length && <div className="text-gray-500 mt-2">Aún no hay ejecuciones.</div>}
        <ul className="list-disc pl-6 mt-2">
          {data?.runs?.map(r => (
            <li key={r.id} className="text-sm">{r.id.slice(0,8)} • {r.status} • {new Date(r.created_at).toLocaleString()}</li>
          ))}
        </ul>
      </section>
    </div>
  )
}

