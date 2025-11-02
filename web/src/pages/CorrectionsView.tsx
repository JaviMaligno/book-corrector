import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api } from '../lib/api'
import { CorrectionsTable } from '../components/CorrectionsTable'
import type { CorrectionRow, Suggestion } from '../lib/types'
import { useState, useMemo } from 'react'
import { 
  listSuggestions, 
  updateSuggestionStatus, 
  bulkUpdateSuggestions,
  acceptAllSuggestions,
  rejectAllSuggestions,
  exportWithAccepted,
  downloadExportedDocument
} from '../lib/suggestions'

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

type StatusFilter = 'all' | 'pending' | 'accepted' | 'rejected'

export default function CorrectionsView() {
  const { runId = '' } = useParams()
  const queryClient = useQueryClient()
  const [selectedDocument, setSelectedDocument] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  // Try to fetch suggestions from backend (server mode)
  const { data: suggestionsResponse, isLoading: suggestionsLoading, error: suggestionsError } = useQuery({
    queryKey: ['suggestions', runId, statusFilter],
    queryFn: async () => {
      const status = statusFilter === 'all' ? undefined : statusFilter
      return await listSuggestions(runId, status)
    },
    retry: false
  })

  // Fallback: fetch JSONL artifacts (legacy mode)
  const { data: artifacts, isLoading: artifactsLoading } = useQuery({
    queryKey: ['artifacts', runId],
    queryFn: async () => {
      const response = await api.get<{ files: string[] }>(`/runs/${runId}/artifacts`)
      return response.data
    },
    enabled: !!suggestionsError // Only fetch if suggestions failed
  })

  const jsonlFiles = artifacts?.files?.filter(f => f.endsWith('.corrections.jsonl')) || []

  const { data: allCorrections, isLoading: correctionsLoading } = useQuery({
    queryKey: ['corrections', runId, jsonlFiles],
    queryFn: async () => {
      if (jsonlFiles.length === 0) return []
      const results = await Promise.all(
        jsonlFiles.map(async (filename) => {
          const response = await api.get(`/runs/artifacts/${runId}/${encodeURIComponent(filename)}`, {
            responseType: 'text'
          })
          const documentName = filename.replace('.corrections.jsonl', '')
          return parseJsonl(response.data, documentName)
        })
      )
      return results.flat()
    },
    enabled: !!suggestionsError && jsonlFiles.length > 0
  })

  // Determine mode: server (suggestions API) or legacy (JSONL)
  const mode = suggestionsResponse ? 'server' : 'legacy'
  const suggestions = suggestionsResponse?.suggestions || []

  // Mutations for server mode
  const acceptMutation = useMutation({
    mutationFn: (id: string) => updateSuggestionStatus(id, 'accepted'),
    onSuccess: () => queryClient.invalidateQueries(['suggestions', runId])
  })

  const rejectMutation = useMutation({
    mutationFn: (id: string) => updateSuggestionStatus(id, 'rejected'),
    onSuccess: () => queryClient.invalidateQueries(['suggestions', runId])
  })

  const bulkAcceptMutation = useMutation({
    mutationFn: (ids: string[]) => bulkUpdateSuggestions(runId, ids, 'accepted'),
    onSuccess: () => queryClient.invalidateQueries(['suggestions', runId])
  })

  const bulkRejectMutation = useMutation({
    mutationFn: (ids: string[]) => bulkUpdateSuggestions(runId, ids, 'rejected'),
    onSuccess: () => queryClient.invalidateQueries(['suggestions', runId])
  })

  const acceptAllMutation = useMutation({
    mutationFn: () => acceptAllSuggestions(runId),
    onSuccess: () => queryClient.invalidateQueries(['suggestions', runId])
  })

  const rejectAllMutation = useMutation({
    mutationFn: () => rejectAllSuggestions(runId),
    onSuccess: () => queryClient.invalidateQueries(['suggestions', runId])
  })

  const exportMutation = useMutation({
    mutationFn: () => exportWithAccepted(runId),
    onSuccess: (blob) => {
      downloadExportedDocument(runId, blob)
    }
  })

  // Stats for server mode
  const stats = useMemo(() => {
    if (mode === 'legacy') return null
    const pending = suggestions.filter(s => s.status === 'pending').length
    const accepted = suggestions.filter(s => s.status === 'accepted').length
    const rejected = suggestions.filter(s => s.status === 'rejected').length
    return { pending, accepted, rejected, total: suggestions.length }
  }, [mode, suggestions])

  // Documents list for legacy mode
  const documents = useMemo(() => {
    if (mode === 'server') return []
    if (!allCorrections) return []
    const uniqueDocs = new Set(allCorrections.map(c => c.document).filter(Boolean))
    return Array.from(uniqueDocs).sort()
  }, [mode, allCorrections])

  // Filter corrections by document in legacy mode
  const corrections = useMemo(() => {
    if (mode === 'server') return []
    if (!allCorrections) return []
    if (selectedDocument === 'all') return allCorrections
    return allCorrections.filter(c => c.document === selectedDocument)
  }, [mode, allCorrections, selectedDocument])

  const isLoading = suggestionsLoading || (suggestionsError && (artifactsLoading || correctionsLoading))

  if (isLoading) {
    return (
      <div className="card p-6 text-center">
        <div className="text-gray-500">Cargando correcciones...</div>
      </div>
    )
  }

  if (mode === 'legacy' && jsonlFiles.length === 0) {
    return (
      <div className="card p-6 text-center">
        <div className="text-gray-500">No se encontraron archivos de correcciones</div>
      </div>
    )
  }

  if (mode === 'server' && suggestions.length === 0 && statusFilter === 'all') {
    return (
      <div className="card p-6 text-center">
        <div className="text-gray-500">No hay sugerencias para este run</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <div className="card p-4">
        <h2 className="text-lg font-semibold text-gray-800">
          Correcciones - Run {runId.slice(0, 8)}
        </h2>
        {mode === 'server' && stats && (
          <p className="text-sm text-gray-600 mt-1">
            {stats.pending} pendientes · {stats.accepted} aceptadas · {stats.rejected} rechazadas
          </p>
        )}
        {mode === 'legacy' && (
          <p className="text-sm text-gray-600 mt-1">
            {documents.length > 1
              ? `${documents.length} documentos procesados · ${allCorrections?.length || 0} correcciones totales`
              : `${allCorrections?.length || 0} correcciones encontradas`
            }
          </p>
        )}
      </div>

      {/* Status Filter Tabs (server mode) */}
      {mode === 'server' && stats && (
        <div className="card p-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-gray-700">Estado:</span>
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                statusFilter === 'all'
                  ? 'bg-brand-ink text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Todas ({stats.total})
            </button>
            <button
              onClick={() => setStatusFilter('pending')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                statusFilter === 'pending'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Pendientes ({stats.pending})
            </button>
            <button
              onClick={() => setStatusFilter('accepted')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                statusFilter === 'accepted'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Aceptadas ({stats.accepted})
            </button>
            <button
              onClick={() => setStatusFilter('rejected')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                statusFilter === 'rejected'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Rechazadas ({stats.rejected})
            </button>
            
            {/* Export button */}
            {stats.accepted > 0 && (
              <>
                <div className="flex-1" />
                <button
                  onClick={() => exportMutation.mutate()}
                  disabled={exportMutation.isPending}
                  className="px-4 py-1.5 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {exportMutation.isPending ? 'Exportando...' : '📥 Descargar DOCX con aceptadas'}
                </button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Document Filter Tabs (legacy mode) */}
      {mode === 'legacy' && documents.length > 1 && (
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

      {/* Corrections Table */}
      <CorrectionsTable
        rows={mode === 'server' ? suggestions : corrections}
        showDocumentColumn={mode === 'legacy' && documents.length > 1 && selectedDocument === 'all'}
        mode={mode}
        onAccept={mode === 'server' ? (id) => acceptMutation.mutate(id) : undefined}
        onReject={mode === 'server' ? (id) => rejectMutation.mutate(id) : undefined}
        onBulkAccept={mode === 'server' ? (ids) => bulkAcceptMutation.mutate(ids) : undefined}
        onBulkReject={mode === 'server' ? (ids) => bulkRejectMutation.mutate(ids) : undefined}
        onAcceptAll={mode === 'server' ? () => acceptAllMutation.mutate() : undefined}
        onRejectAll={mode === 'server' ? () => rejectAllMutation.mutate() : undefined}
        stats={stats}
      />
    </div>
  )
}
