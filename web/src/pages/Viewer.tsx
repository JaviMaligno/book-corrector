import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CorrectionsTable } from '../components/CorrectionsTable'
import { parseJsonl } from '../lib/jsonl'

export default function Viewer(){
  const [jsonl, setJsonl] = useState<string>('')
  const [filename, setFilename] = useState<string>('')
  const [remoteUrl, setRemoteUrl] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string>('')
  const [params] = useSearchParams()
  const data = jsonl ? parseJsonl(jsonl) : []

  useEffect(() => {
    const url = params.get('jsonlUrl')
    if (url) {
      setRemoteUrl(url)
      loadFromUrl(url)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function loadFromUrl(url: string){
    try{
      setLoading(true)
      setError('')
      const res = await fetch(url)
      if(!res.ok){
        throw new Error(`Error ${res.status}`)
      }
      const text = await res.text()
      setJsonl(text)
      setFilename(url)
    }catch(e:any){
      setError(e?.message || 'No se pudo cargar el archivo')
    }finally{
      setLoading(false)
    }
  }

  return (
    <div>
      <section className="card p-4">
        <h2 className="text-base font-medium mb-2">Cargar log JSONL</h2>
        <p className="text-sm text-gray-600 mb-3">Selecciona un archivo <code>.corrections.jsonl</code> generado por el CLI o pega la URL del artefacto para previsualizar las correcciones.</p>
        <input
          type="file"
          accept=".jsonl,.txt,application/jsonl"
          onChange={async (e) => {
            const f = e.target.files?.[0]
            if (!f) return
            const text = await f.text()
            setFilename(f.name)
            setJsonl(text)
          }}
          className="block border rounded p-2 w-full max-w-md"
        />
        <div className="mt-3 grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-2 max-w-3xl">
          <input
            placeholder="https://localhost:8000/artifacts/{runId}/{file}.jsonl"
            className="border rounded px-3 py-2"
            value={remoteUrl}
            onChange={e=>setRemoteUrl(e.target.value)}
          />
          <button className="btn-primary" onClick={()=>loadFromUrl(remoteUrl)} disabled={!remoteUrl || loading}>Cargar</button>
          <button className="px-3 py-2 rounded-md border" onClick={()=>{setJsonl(''); setFilename(''); setError('');}}>Limpiar</button>
        </div>
        {filename && (
          <div className="mt-2 text-sm text-gray-500">Archivo: {filename} • Entradas: {data.length}</div>
        )}
        {loading && <div className="mt-2 text-sm text-gray-500">Cargando…</div>}
        {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
      </section>

      <section className="mt-6">
        <CorrectionsTable rows={data} />
      </section>
    </div>
  )
}
