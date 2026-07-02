import React, { useEffect, useState } from 'react'
import axios from 'axios'

type Agent = { id: string; name: string; status?: string; success_rate?: number; avg_cost?: number }

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios
      .get('/api/agents')
      .then((r) => setAgents(r.data || []))
      .catch(() => setAgents([]))
      .finally(() => setLoading(false))
  }, [])

  const total = agents.length
  const successRate = agents.length ? agents.reduce((s, a) => s + (a.success_rate || 0), 0) / agents.length : 0
  const avgCost = agents.length ? (agents.reduce((s, a) => s + (a.avg_cost || 0), 0) / agents.length).toFixed(2) : '0.00'

  return (
    <div className="p-6">
      <header className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Agents Dashboard</h1>
          <p className="text-sm text-gray-500">Overview of agent health and activity</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="px-4 py-2 bg-blue-600 text-white rounded">Create Agent</button>
          <div className="px-3 py-2 bg-gray-100 rounded">User ▼</div>
        </div>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-white rounded shadow">
          <div className="text-sm text-gray-500">Total Agents</div>
          <div className="text-2xl font-semibold">Total agents: {total}</div>
        </div>
        <div className="p-4 bg-white rounded shadow">
          <div className="text-sm text-gray-500">Avg Success Rate</div>
          <div className="text-2xl font-semibold">Success rate: {(successRate * 100).toFixed(0)}%</div>
        </div>
        <div className="p-4 bg-white rounded shadow">
          <div className="text-sm text-gray-500">Avg Cost</div>
          <div className="text-2xl font-semibold">Avg cost: ${avgCost}</div>
        </div>
      </section>

      <main>
        <h2 className="text-lg font-medium mb-3">Agents</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading && <div className="text-gray-500">Loading...</div>}
          {!loading && agents.length === 0 && <div className="text-gray-500">No agents found.</div>}
          {agents.map((a) => (
            <div key={a.id} className="p-4 bg-white rounded shadow hover:shadow-md">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{a.name}</h3>
                  <div className="text-sm text-gray-500">{a.status || 'idle'}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Success</div>
                  <div className="font-medium">{Math.round((a.success_rate || 0) * 100)}%</div>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <div>Avg cost: ${a.avg_cost ?? '0.00'}</div>
                <button className="text-blue-600">Open</button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
