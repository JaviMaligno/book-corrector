import { useMemo, useState } from 'react'
import type { CorrectionRow, Suggestion } from '../lib/types'

type Props = {
  rows: CorrectionRow[] | Suggestion[]
  showDocumentColumn?: boolean
  mode?: 'legacy' | 'server'
  onAccept?: (id: string) => void
  onReject?: (id: string) => void
  onBulkAccept?: (ids: string[]) => void
  onBulkReject?: (ids: string[]) => void
  onAcceptAll?: () => void
  onRejectAll?: () => void
  stats?: { pending: number; accepted: number; rejected: number; total: number } | null
}

type ViewMode = 'inline' | 'stacked' | 'side'

function isSuggestion(row: CorrectionRow | Suggestion): row is Suggestion {
  return 'id' in row && 'status' in row
}

export function CorrectionsTable({ 
  rows, 
  showDocumentColumn = false,
  mode = 'legacy',
  onAccept,
  onReject,
  onBulkAccept,
  onBulkReject,
  onAcceptAll,
  onRejectAll,
  stats
}: Props) {
  const [query, setQuery] = useState('')
  const [view, setView] = useState<ViewMode>('inline')
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [showAcceptAllModal, setShowAcceptAllModal] = useState(false)
  const [showRejectAllModal, setShowRejectAllModal] = useState(false)

  const filtered = useMemo(() => {
    if (!query) return rows
    const q = query.toLowerCase()
    return rows.filter(r => {
      const original = isSuggestion(r) ? r.before : r.original
      const corrected = isSuggestion(r) ? r.after : r.corrected
      const reason = r.reason || ''
      const sentence = r.sentence || ''
      return (
        original.toLowerCase().includes(q) ||
        corrected.toLowerCase().includes(q) ||
        reason.toLowerCase().includes(q) ||
        sentence.toLowerCase().includes(q)
      )
    })
  }, [rows, query])

  const selectableIds = useMemo(() => {
    if (mode === 'legacy') return []
    return filtered
      .filter(r => isSuggestion(r) && r.status === 'pending')
      .map(r => (r as Suggestion).id)
  }, [mode, filtered])

  const allSelected = selectableIds.length > 0 && selectableIds.every(id => selected.has(id))
  const someSelected = selectableIds.some(id => selected.has(id))

  const toggleAll = () => {
    if (allSelected) {
      setSelected(new Set())
    } else {
      setSelected(new Set(selectableIds))
    }
  }

  const toggleOne = (id: string) => {
    const newSelected = new Set(selected)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelected(newSelected)
  }

  const handleBulkAccept = () => {
    if (onBulkAccept && selected.size > 0) {
      onBulkAccept(Array.from(selected))
      setSelected(new Set())
    }
  }

  const handleBulkReject = () => {
    if (onBulkReject && selected.size > 0) {
      onBulkReject(Array.from(selected))
      setSelected(new Set())
    }
  }

  const handleAcceptAll = () => {
    if (onAcceptAll) {
      onAcceptAll()
      setSelected(new Set())
      setShowAcceptAllModal(false)
    }
  }

  const handleRejectAll = () => {
    if (onRejectAll) {
      onRejectAll()
      setSelected(new Set())
      setShowRejectAllModal(false)
    }
  }

  if (rows.length === 0) {
    return (
      <div className="card p-6 text-center text-gray-500">
        No hay correcciones para mostrar.
      </div>
    )
  }

  return (
    <div className="card p-4">
      {/* Progress Bar (server mode) */}
      {mode === 'server' && stats && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>Progreso de revisión</span>
            <span>{Math.round(((stats.accepted + stats.rejected) / stats.total) * 100)}% completado</span>
          </div>
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden flex">
            <div
              className="bg-green-500"
              style={{ width: `${(stats.accepted / stats.total) * 100}%` }}
              title={`${stats.accepted} aceptadas`}
            />
            <div
              className="bg-yellow-400"
              style={{ width: `${(stats.pending / stats.total) * 100}%` }}
              title={`${stats.pending} pendientes`}
            />
            <div
              className="bg-red-500"
              style={{ width: `${(stats.rejected / stats.total) * 100}%` }}
              title={`${stats.rejected} rechazadas`}
            />
          </div>
          <div className="flex gap-4 text-xs text-gray-600 mt-1">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full" />
              {stats.accepted} aceptadas
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-yellow-400 rounded-full" />
              {stats.pending} pendientes
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-red-500 rounded-full" />
              {stats.rejected} rechazadas
            </span>
          </div>
        </div>
      )}

      {/* Bulk Actions Bar (server mode) */}
      {mode === 'server' && (
        <div className="mb-3 p-3 bg-gray-50 rounded-md border border-gray-200 flex flex-wrap items-center gap-2">
          <input
            type="checkbox"
            checked={allSelected}
            ref={input => {
              if (input) input.indeterminate = someSelected && !allSelected
            }}
            onChange={toggleAll}
            disabled={selectableIds.length === 0}
            className="w-4 h-4"
            title="Seleccionar todas las visibles"
          />
          <span className="text-sm text-gray-700">
            {selected.size > 0 ? `${selected.size} seleccionada(s)` : 'Seleccionar todas'}
          </span>
          
          {selected.size > 0 && (
            <>
              <button
                onClick={handleBulkAccept}
                className="px-3 py-1.5 bg-green-600 text-white rounded-md text-sm font-medium hover:bg-green-700 transition-colors"
              >
                ✓ Aceptar seleccionadas ({selected.size})
              </button>
              <button
                onClick={handleBulkReject}
                className="px-3 py-1.5 bg-red-600 text-white rounded-md text-sm font-medium hover:bg-red-700 transition-colors"
              >
                ✗ Rechazar seleccionadas ({selected.size})
              </button>
            </>
          )}

          <div className="flex-1" />

          {stats && stats.pending > 0 && (
            <>
              <button
                onClick={() => setShowAcceptAllModal(true)}
                className="px-3 py-1.5 bg-green-500 text-white rounded-md text-sm font-medium hover:bg-green-600 transition-colors"
              >
                Aceptar todas pendientes ({stats.pending})
              </button>
              <button
                onClick={() => setShowRejectAllModal(true)}
                className="px-3 py-1.5 bg-red-500 text-white rounded-md text-sm font-medium hover:bg-red-600 transition-colors"
              >
                Rechazar todas pendientes ({stats.pending})
              </button>
            </>
          )}
        </div>
      )}

      {/* Search and View Controls */}
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-3">
        <div className="text-sm text-gray-700">
          Correcciones: <span className="font-medium">{filtered.length}</span>
        </div>
        <div className="flex gap-2">
          <input
            placeholder="Buscar en correcciones..."
            className="border rounded px-3 py-2 w-full md:w-80"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <select
            className="border rounded px-2"
            value={view}
            onChange={e => setView(e.target.value as ViewMode)}
          >
            <option value="inline">Vista inline</option>
            <option value="stacked">Antes / Después</option>
            <option value="side">Lado a lado</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead className="text-left text-gray-700 border-b-2 border-gray-300">
            <tr>
              {mode === 'server' && <th className="py-2 pr-2 font-semibold w-8"></th>}
              <th className="py-2 pr-2 font-semibold">#</th>
              {showDocumentColumn && <th className="py-2 pr-2 font-semibold">Documento</th>}
              <th className="py-2 pr-2 font-semibold">Frase Completa</th>
              <th className="py-2 pr-2 font-semibold">Original → Corregido</th>
              <th className="py-2 pr-2 font-semibold">Motivo</th>
              {mode === 'server' && <th className="py-2 pr-2 font-semibold">Tipo</th>}
              <th className="py-2 pr-2 font-semibold">Línea</th>
              {mode === 'server' && <th className="py-2 pr-2 font-semibold">Estado/Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <TableRow
                key={isSuggestion(r) ? r.id : i}
                row={r}
                index={i + 1}
                view={view}
                showDocumentColumn={showDocumentColumn}
                mode={mode}
                selected={isSuggestion(r) ? selected.has(r.id) : false}
                onToggleSelect={isSuggestion(r) ? () => toggleOne(r.id) : undefined}
                onAccept={isSuggestion(r) && onAccept ? () => onAccept(r.id) : undefined}
                onReject={isSuggestion(r) && onReject ? () => onReject(r.id) : undefined}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Confirmation Modals */}
      {showAcceptAllModal && (
        <ConfirmModal
          title="Aceptar todas las sugerencias pendientes"
          message={`¿Estás seguro de que quieres aceptar las ${stats?.pending} sugerencias pendientes? Se aplicarán al documento final.`}
          confirmText="Aceptar todas"
          confirmClass="bg-green-600 hover:bg-green-700"
          onConfirm={handleAcceptAll}
          onCancel={() => setShowAcceptAllModal(false)}
        />
      )}
      {showRejectAllModal && (
        <ConfirmModal
          title="Rechazar todas las sugerencias pendientes"
          message={`¿Estás seguro de que quieres rechazar las ${stats?.pending} sugerencias pendientes? No se aplicarán al documento final.`}
          confirmText="Rechazar todas"
          confirmClass="bg-red-600 hover:bg-red-700"
          onConfirm={handleRejectAll}
          onCancel={() => setShowRejectAllModal(false)}
        />
      )}
    </div>
  )
}

type RowProps = {
  row: CorrectionRow | Suggestion
  index: number
  view: ViewMode
  showDocumentColumn: boolean
  mode?: 'legacy' | 'server'
  selected?: boolean
  onToggleSelect?: () => void
  onAccept?: () => void
  onReject?: () => void
}

function TableRow({ row, index, view, showDocumentColumn, mode = 'legacy', selected, onToggleSelect, onAccept, onReject }: RowProps) {
  const suggestion = isSuggestion(row) ? row : null
  const original = suggestion ? suggestion.before : row.original
  const corrected = suggestion ? suggestion.after : row.corrected
  const isPending = suggestion?.status === 'pending'
  const isAccepted = suggestion?.status === 'accepted'
  const isRejected = suggestion?.status === 'rejected'
  
  const rowClasses = `border-b last:border-0 align-top hover:bg-gray-50 ${
    isAccepted ? 'bg-green-50 opacity-75' : isRejected ? 'bg-red-50 opacity-75' : ''
  }`

  return (
    <tr className={rowClasses}>
      {mode === 'server' && (
        <td className="py-3 pr-2">
          {isPending && (
            <input
              type="checkbox"
              checked={selected}
              onChange={onToggleSelect}
              className="w-4 h-4"
            />
          )}
        </td>
      )}

      <td className="py-3 pr-2 text-gray-500 text-center">{index}</td>

      {showDocumentColumn && (
        <td className="py-3 pr-2 text-gray-700 font-medium max-w-[200px] truncate" title={row.document}>
          {row.document}
        </td>
      )}

      <td className="py-3 pr-2 max-w-[600px]">
        {view === 'inline' && <InlineView row={row} />}
        {view === 'stacked' && <StackedView row={row} />}
        {view === 'side' && <SideView row={row} />}
      </td>

      <td className="py-3 pr-2 whitespace-nowrap">
        <span className="line-through text-red-600 mr-1">{original}</span>
        <span className="text-gray-400">→</span>
        <span className="text-green-600 font-medium ml-1">{corrected}</span>
      </td>

      <td className="py-3 pr-2 text-gray-700 max-w-[400px]">{row.reason}</td>

      {mode === 'server' && suggestion && (
        <td className="py-3 pr-2">
          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
            suggestion.suggestion_type === 'ortografia' ? 'bg-red-100 text-red-700' :
            suggestion.suggestion_type === 'puntuacion' ? 'bg-blue-100 text-blue-700' :
            suggestion.suggestion_type === 'estilo' ? 'bg-purple-100 text-purple-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {suggestion.suggestion_type}
          </span>
        </td>
      )}

      <td className="py-3 pr-2 text-gray-500 text-center">{row.line ?? '-'}</td>

      {mode === 'server' && suggestion && (
        <td className="py-3 pr-2">
          {isPending && (
            <div className="flex gap-1">
              <button
                onClick={onAccept}
                className="px-2 py-1 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 transition-colors"
                title="Aceptar"
              >
                ✓
              </button>
              <button
                onClick={onReject}
                className="px-2 py-1 bg-red-600 text-white rounded text-xs font-medium hover:bg-red-700 transition-colors"
                title="Rechazar"
              >
                ✗
              </button>
            </div>
          )}
          {isAccepted && (
            <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700">
              ✓ Aceptada
            </span>
          )}
          {isRejected && (
            <span className="inline-block px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-700">
              ✗ Rechazada
            </span>
          )}
        </td>
      )}
    </tr>
  )
}

function InlineView({ row }: { row: CorrectionRow | Suggestion }) {
  const sentence = row.sentence || row.context || ''
  const original = isSuggestion(row) ? row.before : row.original
  const corrected = isSuggestion(row) ? row.after : row.corrected

  // Resaltar el texto original en rojo tachado y el corregido en verde
  const parts = sentence.split(original)

  if (parts.length === 1) {
    // No se encontró el original en la frase, mostrar la frase completa
    return <span className="text-gray-800">{sentence}</span>
  }

  return (
    <span className="text-gray-800">
      {parts[0]}
      <span className="bg-red-100 line-through text-red-700 font-medium px-0.5">{original}</span>
      <span className="bg-green-100 text-green-700 font-medium px-0.5">{corrected}</span>
      {parts.slice(1).join(original)}
    </span>
  )
}

function StackedView({ row }: { row: CorrectionRow | Suggestion }) {
  const sentence = row.sentence || row.context || ''
  const original = isSuggestion(row) ? row.before : row.original
  const corrected = isSuggestion(row) ? row.after : row.corrected

  const before = sentence
  const after = sentence.replace(original, corrected)

  return (
    <div className="space-y-2">
      <div>
        <div className="text-xs text-gray-500 mb-1">Antes</div>
        <div className="text-gray-800 bg-red-50 border-l-2 border-red-300 pl-2 py-1">
          {before}
        </div>
      </div>
      <div>
        <div className="text-xs text-gray-500 mb-1">Después</div>
        <div className="text-gray-800 bg-green-50 border-l-2 border-green-300 pl-2 py-1">
          {after}
        </div>
      </div>
    </div>
  )
}

function SideView({ row }: { row: CorrectionRow | Suggestion }) {
  const sentence = row.sentence || row.context || ''
  const original = isSuggestion(row) ? row.before : row.original
  const corrected = isSuggestion(row) ? row.after : row.corrected

  const before = sentence
  const after = sentence.replace(original, corrected)

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div>
        <div className="text-xs text-gray-500 mb-1">Antes</div>
        <div className="text-gray-800 bg-red-50 border border-red-200 rounded px-2 py-1 text-xs">
          {before}
        </div>
      </div>
      <div>
        <div className="text-xs text-gray-500 mb-1">Después</div>
        <div className="text-gray-800 bg-green-50 border border-green-200 rounded px-2 py-1 text-xs">
          {after}
        </div>
      </div>
    </div>
  )
}

type ConfirmModalProps = {
  title: string
  message: string
  confirmText: string
  confirmClass: string
  onConfirm: () => void
  onCancel: () => void
}

function ConfirmModal({ title, message, confirmText, confirmClass, onConfirm, onCancel }: ConfirmModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">{title}</h3>
        <p className="text-gray-700 mb-6">{message}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-md text-sm font-medium text-white transition-colors ${confirmClass}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
