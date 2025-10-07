import { Link, Outlet, useLocation } from 'react-router-dom'
import '../index.css'

export default function Layout(){
  const loc = useLocation()
  const tab = (path: string, label: string) => (
    <Link to={path} className={`px-3 py-2 rounded-md text-sm ${loc.pathname===path? 'bg-[color:var(--ink)] text-white' : 'text-[color:var(--ink)]/80 hover:bg-[color:var(--ink)]/10'}`}>{label}</Link>
  )
  return (
    <div className="min-h-screen" style={{background: 'var(--paper)'}}>
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-6 rounded-sm" style={{background: 'linear-gradient(180deg, var(--ink), var(--teal))'}} />
            <h1 className="text-lg font-semibold text-[color:var(--ink)]">Corrector</h1>
          </div>
          <nav className="flex gap-2">
            {tab('/', 'Visor JSONL')}
            {tab('/projects', 'Proyectos')}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-4">
        <Outlet />
      </main>
    </div>
  )
}

