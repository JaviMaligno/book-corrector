import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import '../index.css'

export default function Layout(){
  const loc = useLocation()
  const { user, isAuthenticated, logout } = useAuth()

  const tab = (path: string, label: string) => (
    <Link to={path} className={`px-3 py-2 rounded-md text-sm ${loc.pathname===path? 'bg-brand-ink text-white' : 'text-brand-ink/80 hover:bg-brand-ink/10'}`}>{label}</Link>
  )

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error('Error during logout:', error)
    }
  }

  return (
    <div className="min-h-screen bg-brand-paper">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-6 rounded-sm bg-gradient-to-b from-brand-ink to-brand-teal" />
            <h1 className="text-lg font-semibold text-brand-ink">Corrector</h1>
            {isAuthenticated && user && (
              <span className="text-sm text-gray-600 ml-2">({user.email})</span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <nav className="flex gap-2">
              {tab('/projects', 'Proyectos')}
              {tab('/viewer', 'Visor JSONL')}
            </nav>
            {isAuthenticated ? (
              <button
                onClick={handleLogout}
                className="px-3 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
              >
                Cerrar sesión
              </button>
            ) : (
              <div className="text-sm text-gray-600">
                Necesitas iniciar sesión para ver proyectos
              </div>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-4">
        <Outlet />
      </main>
    </div>
  )
}

