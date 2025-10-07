import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api, } from '../lib/api'
import { API_URL } from '../lib/env'

type Run = { id: string; project_id: string; status: string; created_at: string }

export default function RunDetail(){
  const { runId = '' } = useParams()
  const run = useQuery({
    queryKey: ['run', runId],
    queryFn: async () => (await api.get<Run>(`/runs/${runId}`)).data,
    refetchInterval: 2000
  })
  const artifacts = useQuery({
    queryKey: ['artifacts', runId],
    queryFn: async () => (await api.get<{ files: string[] }>(`/runs/${runId}/artifacts`)).data,
    refetchInterval: 3000
  })

  const files = artifacts.data?.files || []

  return (
    <div className="space-y-6">
      <section className="card p-4">
        <h2 className="text-base font-medium">Run</h2>
        <div className="text-sm text-gray-600">{run.data?.id} — {run.data?.status}</div>
      </section>

      <section className="card p-4">
        <h3 className="text-base font-medium mb-2">Artefactos</h3>
        {!files.length && <div className="text-gray-500">Aún no hay artefactos.</div>}
        <ul className="list-disc pl-6">
          {files.map(f => {
            const href = `${API_URL}/artifacts/${runId}/${encodeURIComponent(f)}`
            const isJsonl = f.toLowerCase().endsWith('.jsonl')
            const viewer = `/?jsonlUrl=${encodeURIComponent(href)}`
            return (
              <li key={f} className="text-sm flex items-center gap-3">
                <a className="text-[color:var(--ink)] underline" href={href} target="_blank" rel="noreferrer">{f}</a>
                {isJsonl && (
                  <a className="px-2 py-1 border rounded text-[color:var(--ink)] hover:bg-[color:var(--ink)]/10" href={viewer}>
                    Ver en visor
                  </a>
                )}
              </li>
            )
          })}
        </ul>
      </section>
    </div>
  )
}
