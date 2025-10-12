import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { CorrectionsTable } from '../components/CorrectionsTable'
import type { CorrectionRow } from '../lib/types'

function parseJsonl(text: string): CorrectionRow[] {
  return text
    .trim()
    .split('\n')
    .filter(line => line.trim())
    .map(line => {
      try {
        return JSON.parse(line) as CorrectionRow
      } catch {
        return null
      }
    })
    .filter((row): row is CorrectionRow => row !== null)
}

export default function CorrectionsView() {
  const { runId = '' } = useParams()

  const { data: artifacts, isLoading: artifactsLoading } = useQuery({
    queryKey: ['artifacts', runId],
    queryFn: async () => {
      const response = await api.get<{ files: string[] }>(`/runs/${runId}/artifacts`)
      return response.data
    }
  })

  // Buscar el archivo .corrections.jsonl
  const jsonlFile = artifacts?.files?.find(f => f.endsWith('.corrections.jsonl'))

  const { data: corrections, isLoading: correctionsLoading, error } = useQuery({
    queryKey: ['corrections', runId, jsonlFile],
    queryFn: async () => {
      if (!jsonlFile) return []
      const response = await api.get(`/runs/artifacts/${runId}/${encodeURIComponent(jsonlFile)}`, {
        responseType: 'text'
      })
      return parseJsonl(response.data)
    },
    enabled: !!jsonlFile
  })

  if (artifactsLoading || correctionsLoading) {
    return (
      <div className="card p-6 text-center">
        <div className="text-gray-500">Cargando correcciones...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6 text-center">
        <div className="text-red-600">Error al cargar correcciones</div>
      </div>
    )
  }

  if (!jsonlFile) {
    return (
      <div className="card p-6 text-center">
        <div className="text-gray-500">No se encontró archivo de correcciones</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <h2 className="text-lg font-semibold text-gray-800">
          Correcciones - Run {runId.slice(0, 8)}
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Mostrando todas las correcciones encontradas en este documento
        </p>
      </div>

      <CorrectionsTable rows={corrections || []} />
    </div>
  )
}
