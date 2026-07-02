import React from 'react'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold">Agent Framework — Dashboard</h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto p-4">
        <section className="mb-6">
          <h2 className="text-xl font-semibold">Real-time Monitoring</h2>
          <div className="mt-4 p-4 bg-white rounded shadow-sm">
            <p>Monitoring stub — connect to `/api/monitoring` or WebSocket for live data.</p>
          </div>
        </section>
        <section>
          <h2 className="text-xl font-semibold">Agents</h2>
          <div className="mt-4 p-4 bg-white rounded shadow-sm">Agent list placeholder</div>
        </section>
      </main>
    </div>
  )
}
