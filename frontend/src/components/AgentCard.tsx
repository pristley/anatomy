import React from 'react'

type Props = {
  id: string
  name: string
  status?: string
  successRate?: number
}

export default function AgentCard({ id, name, status = 'idle', successRate = 0 }: Props) {
  return (
    <div className="p-4 bg-white rounded shadow">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">{name}</div>
          <div className="text-xs text-gray-500">id: {id}</div>
        </div>
        <div className="text-sm text-gray-600">{status}</div>
      </div>
      <div className="mt-3 text-sm">Success: {(successRate * 100).toFixed(0)}%</div>
    </div>
  )
}
