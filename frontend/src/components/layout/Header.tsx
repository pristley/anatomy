import React from 'react'
import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link to="/" className="text-xl font-bold">Agent Framework</Link>
          <nav className="hidden md:flex space-x-3 text-sm text-gray-600">
            <Link to="/monitoring" className="hover:underline">Monitoring</Link>
            <Link to="/chat" className="hover:underline">Chat</Link>
            <Link to="/memory" className="hover:underline">Memory</Link>
          </nav>
        </div>
        <div className="flex items-center space-x-4">
          <button className="text-sm px-3 py-1 border rounded">Help</button>
          <div className="text-sm">User</div>
        </div>
      </div>
    </header>
  )
}
