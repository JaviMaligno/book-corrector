import { useMemo, useState } from 'react'
import type { CorrectionRow } from '../lib/types'

type Props = {
  rows: CorrectionRow[]
  showDocumentColumn?: boolean
}

type ViewMode = 'inline' | 'stacked' | 'side'

export function CorrectionsTable({ rows, showDocumentColumn = false }: Props) {
  const [query, setQuery] = useState('')
  const [view, setView] = useState<ViewMode>('inline')

  const filtered = useMemo(() => {
    if (!query) return rows
    const q = query.toLowerCase()
    return rows.filter(r =>
      (r.original && r.original.toLowerCase().includes(q)) ||
      (r.corrected && r.corrected.toLowerCase().includes(q)) ||
      (r.reason && r.reason.toLowerCase().includes(q)) ||
      (r.sentence && r.sentence.toLowerCase().includes(q))
    )
  }, [rows, query])

  if (rows.length === 0) {
    return (
      <div className="card p-6 text-center text-gray-500">
        No hay correcciones para mostrar.
      </div>
    )
  }

  return (
    <div className="card p-4">
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

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead className="text-left text-gray-700 border-b-2 border-gray-300">
            <tr>
              <th className="py-2 pr-2 font-semibold">#</th>
              {showDocumentColumn && <th className="py-2 pr-2 font-semibold">Documento</th>}
              <th className="py-2 pr-2 font-semibold">Frase Completa</th>
              <th className="py-2 pr-2 font-semibold">Original → Corregido</th>
              <th className="py-2 pr-2 font-semibold">Motivo</th>
              <th className="py-2 pr-2 font-semibold">Línea</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <TableRow key={i} row={r} index={i + 1} view={view} showDocumentColumn={showDocumentColumn} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

type RowProps = {
  row: CorrectionRow
  index: number
  view: ViewMode
  showDocumentColumn: boolean
}

function TableRow({ row, index, view, showDocumentColumn }: RowProps) {
  return (
    <tr className="border-b last:border-0 align-top hover:bg-gray-50">
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
        <span className="line-through text-red-600 mr-1">{row.original}</span>
        <span className="text-gray-400">→</span>
        <span className="text-green-600 font-medium ml-1">{row.corrected}</span>
      </td>

      <td className="py-3 pr-2 text-gray-700 max-w-[400px]">{row.reason}</td>

      <td className="py-3 pr-2 text-gray-500 text-center">{row.line ?? '-'}</td>
    </tr>
  )
}

function InlineView({ row }: { row: CorrectionRow }) {
  const sentence = row.sentence || row.context || ''
  const original = row.original

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
      <span className="bg-green-100 text-green-700 font-medium px-0.5">{row.corrected}</span>
      {parts.slice(1).join(original)}
    </span>
  )
}

function StackedView({ row }: { row: CorrectionRow }) {
  const sentence = row.sentence || row.context || ''
  const original = row.original
  const corrected = row.corrected

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

function SideView({ row }: { row: CorrectionRow }) {
  const sentence = row.sentence || row.context || ''
  const original = row.original
  const corrected = row.corrected

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
