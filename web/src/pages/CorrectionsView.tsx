import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { CorrectionsTable } from '../components/CorrectionsTable'
import type { CorrectionRow } from '../lib/types'
import { useState, useMemo } from 'react'

function parseJsonl(text: string, documentName: string): CorrectionRow[] {
  return text
    .trim()
    .split('\n')
    .filter(line => line.trim())
    .map(line => {
      try {
        const row = JSON.parse(line) as CorrectionRow
        return { ...row, document: documentName }
      } catch {
        return null
      }
    })
    .filter((row): row is CorrectionRow => row !== null)
}

export default function CorrectionsView() {
  const { runId = '' } = useParams()
  const [selectedDocument, setSelectedDocument] = useState<string>('all')

  const { data: artifacts, isLoading: artifactsLoading } = useQuery({
    queryKey: ['artifacts', runId],
    queryFn: async () => {
      const response = await api.get<{ files: string[] }>(`/runs/${runId}/artifacts`)
      return response.data
    }
  })

  // Buscar TODOS los archivos .corrections.jsonl
  const jsonlFiles = artifacts?.files?.filter(f => f.endsWith('.corrections.jsonl')) || []

  const { data: allCorrections, isLoading: correctionsLoading, error } = useQuery({
    queryKey: ['corrections', runId, jsonlFiles],
    queryFn: async () => {
      if (jsonlFiles.length === 0) return []

      // Cargar todos los archivos JSONL en paralelo
      const results = await Promise.all(
        jsonlFiles.map(async (filename) => {
          const response = await api.get(`/runs/artifacts/${runId}/${encodeURIComponent(filename)}`, {
            responseType: 'text'
          })
          // Extraer nombre del documento del nombre del archivo (sin .corrections.jsonl)
          const documentName = filename.replace('.corrections.jsonl', '')
          return parseJsonl(response.data, documentName)
        })
      )

      // Aplanar el array de arrays
      return results.flat()
    },
    enabled: jsonlFiles.length > 0
  })

  // Obtener lista única de documentos
  const documents = useMemo(() => {
    if (!allCorrections) return []
    const uniqueDocs = new Set(allCorrections.map(c => c.document).filter(Boolean))
    return Array.from(uniqueDocs).sort()
  }, [allCorrections])

  // Filtrar correcciones según documento seleccionado
  const corrections = useMemo(() => {
    if (!allCorrections) return []
    if (selectedDocument === 'all') return allCorrections
    return allCorrections.filter(c => c.document === selectedDocument)
  }, [allCorrections, selectedDocument])

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

  if (jsonlFiles.length === 0) {
    return (
      <div className="card p-6 text-center">
        <div className="text-gray-500">No se encontraron archivos de correcciones</div>
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
          {documents.length > 1
            ? `${documents.length} documentos procesados · ${allCorrections?.length || 0} correcciones totales`
            : `${allCorrections?.length || 0} correcciones encontradas`
          }
        </p>
      </div>

      {/* Pestañas para filtrar por documento */}
      {documents.length > 1 && (
        <div className="card p-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-gray-700">Filtrar por documento:</span>
            <button
              onClick={() => setSelectedDocument('all')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                selectedDocument === 'all'
                  ? 'bg-brand-ink text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Todos ({allCorrections?.length || 0})
            </button>
            {documents.map(doc => {
              const count = allCorrections?.filter(c => c.document === doc).length || 0
              return (
                <button
                  key={doc}
                  onClick={() => setSelectedDocument(doc)}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    selectedDocument === doc
                      ? 'bg-brand-ink text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {doc} ({count})
                </button>
              )
            })}
          </div>
        </div>
      )}

      <CorrectionsTable rows={corrections || []} showDocumentColumn={documents.length > 1 && selectedDocument === 'all'} />
    </div>
  )
}
