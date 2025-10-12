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

  const hasCorrections = files.some(f => f.endsWith('.corrections.jsonl'))

  return (
    <div className="space-y-6">
      <section className="card p-4">
        <h2 className="text-base font-medium">Run</h2>
        <div className="text-sm text-gray-600">{run.data?.id} — {run.data?.status}</div>
      </section>

      {hasCorrections && (
        <section className="card p-4 bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-medium text-blue-900">Correcciones disponibles</h3>
              <p className="text-sm text-gray-600">Haz clic en el botón para ver el detalle</p>
            </div>
            <a
              href={`/runs/${runId}/corrections`}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
              Ver tabla de correcciones
            </a>
          </div>
        </section>
      )}

      <section className="card p-4">
        <h3 className="text-base font-medium mb-2">Artefactos</h3>
        {!files.length && <div className="text-gray-500">Aún no hay artefactos.</div>}
        <ul className="list-disc pl-6">
          {files.map(f => {
            const href = `${API_URL}/artifacts/${runId}/${encodeURIComponent(f)}`
            return (
              <li key={f} className="text-sm">
                <a className="text-brand-ink underline" href={href} target="_blank" rel="noreferrer">{f}</a>
              </li>
            )
          })}
        </ul>
      </section>
    </div>
  )
}
