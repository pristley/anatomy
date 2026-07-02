import React, { useEffect, useState } from 'react'
import axios from 'axios'

export default function Memory() {
  const [tab, setTab] = useState<'episodic' | 'semantic' | 'tools'>('episodic')
  const [query, setQuery] = useState('')
  const [episodic, setEpisodic] = useState<any[]>([])
  const [semantic, setSemantic] = useState<any[]>([])
  const [tools, setTools] = useState<any[]>([])
  const [toolParams, setToolParams] = useState('{}')
  const [toolResult, setToolResult] = useState<any>(null)

  useEffect(() => {
    axios.get('/api/memory/semantic').then((r) => setSemantic(r.data || [])).catch(() => setSemantic([]))
    axios.get('/api/tools').then((r) => setTools(r.data || [])).catch(() => setTools([]))
  }, [])

  const search = () => {
    axios
      .get('/api/memory/search', { params: { q: query } })
      .then((r) => setEpisodic(r.data || []))
      .catch(() => setEpisodic([]))
  }

  const callTool = async (name: string) => {
    try {
      const params = JSON.parse(toolParams || '{}')
      const r = await axios.post(`/api/tools/${encodeURIComponent(name)}/invoke`, params)
      setToolResult(r.data)
    } catch (e: any) {
      setToolResult({ error: e.message })
    }
  }

  return (
    <div className="p-6">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Memory</h1>
        <div className="text-sm text-gray-500">Explore episodic and semantic memory</div>
      </header>

      <div className="mb-4">
        <nav className="flex gap-2">
          <button className={`px-3 py-1 rounded ${tab === 'episodic' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`} onClick={() => setTab('episodic')}>
            Episodic
          </button>
          <button className={`px-3 py-1 rounded ${tab === 'semantic' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`} onClick={() => setTab('semantic')}>
            Semantic
          </button>
          <button className={`px-3 py-1 rounded ${tab === 'tools' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`} onClick={() => setTab('tools')}>
            Tools
          </button>
        </nav>
      </div>

      {tab === 'episodic' && (
        <div className="bg-white p-4 rounded shadow">
          <div className="flex gap-2 mb-3">
            <input className="flex-1 border rounded px-3 py-2" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search experiences..." />
            <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={search}>
              Search
            </button>
          </div>
          <div className="space-y-3 max-h-64 overflow-auto">
            {episodic.length === 0 && <div className="text-gray-500">No results</div>}
            {episodic.map((r: any, i: number) => (
              <div key={i} className="p-2 border rounded">
                <div className="text-sm font-medium">{r.input}</div>
                <div className="text-xs text-gray-500">score: {r.score} • {new Date(r.timestamp).toLocaleString()}</div>
                <div className="mt-1 text-sm">{String(r.output).slice(0, 300)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'semantic' && (
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-medium mb-2">Patterns</h3>
          <div className="space-y-2">
            {semantic.length === 0 && <div className="text-gray-500">No semantic patterns</div>}
            {semantic.map((s: any, i: number) => (
              <div key={i} className="p-2 border rounded">
                <div className="font-medium">{s.category}</div>
                <div className="text-xs text-gray-500">count: {s.count} • avg_confidence: {s.avg_confidence}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'tools' && (
        <div className="bg-white p-4 rounded shadow">
          <h3 className="font-medium mb-2">Tool Registry</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            {tools.map((t: any) => (
              <div key={t.name} className="p-2 border rounded">
                <div className="font-medium">{t.name}</div>
                <div className="text-xs text-gray-500">{t.description}</div>
              </div>
            ))}
          </div>

          <div className="mt-4">
            <h4 className="font-medium mb-2">Tool Tester</h4>
            <div className="flex gap-2 mb-2">
              <select className="border rounded px-2 py-1" id="tool-select">
                {tools.map((t: any) => (
                  <option key={t.name} value={t.name}>
                    {t.name}
                  </option>
                ))}
              </select>
              <textarea className="flex-1 border rounded p-2" value={toolParams} onChange={(e) => setToolParams(e.target.value)} />
            </div>
            <div className="flex gap-2">
              <button
                className="px-4 py-2 bg-green-600 text-white rounded"
                onClick={() => {
                  const sel = (document.getElementById('tool-select') as HTMLSelectElement).value
                  callTool(sel)
                }}
              >
                Invoke
              </button>
              <div className="text-sm text-gray-500">Result:</div>
              <pre className="text-xs bg-gray-50 p-2 rounded">{JSON.stringify(toolResult, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
