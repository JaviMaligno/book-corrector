import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'
import Viewer from './pages/Viewer'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import RunDetail from './pages/RunDetail'
import Layout from './layouts/Layout'

const queryClient = new QueryClient()

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <Viewer /> },
      { path: '/projects', element: <Projects /> },
      { path: '/projects/:projectId', element: <ProjectDetail /> },
      { path: '/runs/:runId', element: <RunDetail /> }
    ]
  }
])

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>
)
