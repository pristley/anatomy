import React from 'react'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 text-gray-900">
        <Header />
        <main className="max-w-7xl mx-auto p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/memory" element={<Memory />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
