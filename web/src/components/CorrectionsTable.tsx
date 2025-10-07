import React, { useMemo, useState } from 'react'
import type { CorrectionRow } from '../lib/types'
import { ContextSnippet } from './ContextSnippet'

type Props = { rows: CorrectionRow[] }

export function CorrectionsTable({ rows }: Props) {
  const [query, setQuery] = useState('')
  const [view, setView] = useState<'inline' | 'stacked' | 'side'>('inline')

  const filtered = useMemo(() => {
    if (!query) return rows
    const q = query.toLowerCase()
    return rows.filter(r =>
      (r.original && r.original.toLowerCase().includes(q)) ||
      (r.corrected && r.corrected.toLowerCase().includes(q)) ||
      (r.reason && r.reason.toLowerCase().includes(q)) ||
      (r.context && r.context.toLowerCase().includes(q)) ||
      (r.sentence && r.sentence.toLowerCase().includes(q))
    )
  }, [rows, query])

  if (rows.length === 0) {
    return (
      <div className="card p-6 text-center text-gray-500">
        Sube un archivo JSONL para ver las correcciones.
      </div>
    )
  }

  return (
    <div className="card p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-3">
        <div className="text-sm text-gray-700">Correcciones: <span className="font-medium">{filtered.length}</span></div>
        <div className="flex gap-2">
          <input
            placeholder="Buscar (palabra, razón, contexto)"
            className="border rounded px-3 py-2 w-full md:w-80"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <select className="border rounded px-2" value={view} onChange={e => setView(e.target.value as any)}>
            <option value="inline">Vista en línea</option>
            <option value="stacked">Antes / Después</option>
            <option value="side">Lado a lado</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-gray-600 border-b">
            <tr>
              <th className="py-2 pr-2">#</th>
              <th className="py-2 pr-2">Frase / Contexto</th>
              <th className="py-2 pr-2">Original → Corregido</th>
              <th className="py-2 pr-2">Motivo</th>
              <th className="py-2 pr-2">Línea</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((r, i) => (
              <tr key={i} className="border-b last:border-0 align-top">
                <td className="py-2 pr-2 text-gray-500">{i + 1}</td>
                <td className="py-2 pr-2 max-w-[560px]">
                  {view === 'inline' && (
                    <ContextSnippet text={r.sentence || r.context || ''} target={r.original} replacement={r.corrected} mode="inline" />
                  )}
                  {view === 'stacked' && (
                    <div className="space-y-1">
                      <div className="text-gray-500 text-xs">Antes</div>
                      <ContextSnippet text={r.sentence || r.context || ''} target={r.original} mode="before" />
                      <div className="text-gray-500 text-xs mt-2">Después</div>
                      <ContextSnippet text={r.sentence || r.context || ''} target={r.original} replacement={r.corrected} mode="after" />
                    </div>
                  )}
                  {view === 'side' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <div className="text-gray-500 text-xs mb-1">Antes</div>
                        <ContextSnippet text={r.sentence || r.context || ''} target={r.original} mode="before" />
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs mb-1">Después</div>
                        <ContextSnippet text={r.sentence || r.context || ''} target={r.original} replacement={r.corrected} mode="after" />
                      </div>
                    </div>
                  )}
                </td>
                <td className="py-2 pr-2 whitespace-nowrap">
                  <span className="line-through text-[color:var(--red)] mr-1">{r.original}</span>
                  <span className="text-gray-400">→</span>
                  <span className="text-[color:var(--teal)] font-medium ml-1">{r.corrected}</span>
                </td>
                <td className="py-2 pr-2 text-gray-700 max-w-[320px]">{r.reason}</td>
                <td className="py-2 pr-2 text-gray-500">{r.line ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

