import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { Link } from 'react-router-dom'
import { useState } from 'react'

type Project = {
  id: string
  name: string
  variant?: string
  mode?: string
  created_at: string
}

export default function Projects(){
  const qc = useQueryClient()
  const { data } = useQuery({
    queryKey: ['projects'],
    queryFn: async () => (await api.get<Project[]>('/projects')).data
  })

  const [name, setName] = useState('Proyecto de ejemplo')
  const [variant, setVariant] = useState('es-ES')
  const [mode, setMode] = useState('rapido')

  const create = useMutation({
    mutationFn: async () => (await api.post<Project>('/projects', { name, variant, mode })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] })
  })

  return (
    <div className="space-y-6">
      <section className="card p-4">
        <h2 className="text-base font-medium mb-3">Nuevo proyecto</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <input className="border rounded px-3 py-2" value={name} onChange={e=>setName(e.target.value)} placeholder="Nombre" />
          <select className="border rounded px-3 py-2" value={variant} onChange={e=>setVariant(e.target.value)}>
            <option>es-ES</option>
            <option>es-MX</option>
          </select>
          <select className="border rounded px-3 py-2" value={mode} onChange={e=>setMode(e.target.value)}>
            <option value="rapido">Rápido</option>
            <option value="profesional">Profesional</option>
          </select>
          <button className="btn-primary" onClick={()=>create.mutate()} disabled={create.isPending}>Crear</button>
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-base font-medium mb-3">Proyectos</h2>
        {!data?.length && <div className="text-gray-500">Aún no hay proyectos.</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data?.map(p => (
            <Link to={`/projects/${p.id}`} key={p.id} className="border rounded p-3 hover:bg-gray-50">
              <div className="text-[color:var(--ink)] font-medium">{p.name}</div>
              <div className="text-sm text-gray-500">{p.variant} • {p.mode} • {new Date(p.created_at).toLocaleString()}</div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

