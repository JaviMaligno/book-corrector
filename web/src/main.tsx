import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import RunDetail from './pages/RunDetail'
import CorrectionsView from './pages/CorrectionsView'
import Login from './pages/Login'
import Register from './pages/Register'
import Layout from './layouts/Layout'
import { AuthProvider } from './contexts/AuthContext'

const queryClient = new QueryClient()

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <Projects /> },
      { path: '/projects', element: <Projects /> },
      { path: '/projects/:projectId', element: <ProjectDetail /> },
      { path: '/runs/:runId', element: <RunDetail /> },
      { path: '/runs/:runId/corrections', element: <CorrectionsView /> },
      { path: '/login', element: <Login /> },
      { path: '/register', element: <Register /> }
    ]
  }
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
)
