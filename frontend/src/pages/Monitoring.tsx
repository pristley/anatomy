import React, { useEffect, useState } from 'react'
import axios from 'axios'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

type MetricPoint = { time: string; rps: number; latency: number; cost: number }

export default function Monitoring() {
  const [data, setData] = useState<MetricPoint[]>([])
  const [timeline, setTimeline] = useState<any[]>([])
  const [toolLog, setToolLog] = useState<any[]>([])

  useEffect(() => {
    const fetchOnce = () => {
      axios
        .get('/api/monitoring')
        .then((r) => {
          setData(r.data?.timeseries ?? mockData())
          setTimeline(r.data?.timeline ?? [])
          setToolLog(r.data?.tools ?? [])
        })
        .catch(() => {
          setData(mockData())
          setTimeline([])
          setToolLog([])
        })
    }
    fetchOnce()
    const t = setInterval(fetchOnce, 5000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="p-6">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Monitoring</h1>
        <div className="text-sm text-gray-500">Live metrics (updates every 5s)</div>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-white rounded shadow h-80">
          <h3 className="font-medium mb-2">Requests / sec</h3>
          <ResponsiveContainer width="100%" height="85%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="rps" stroke="#8884d8" dot={false} />
              <Line type="monotone" dataKey="latency" stroke="#82ca9d" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="p-4 bg-white rounded shadow">
          <h3 className="font-medium mb-2">Execution Timeline</h3>
          <div className="space-y-2 max-h-80 overflow-auto">
            {timeline.length === 0 && <div className="text-gray-500">No timeline events</div>}
            {timeline.map((t, i) => (
              <div key={i} className="p-2 border rounded">
                <div className="text-sm font-medium">{t.step}</div>
                <div className="text-xs text-gray-500">{t.duration_ms} ms</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="col-span-2 p-4 bg-white rounded shadow">
          <h3 className="font-medium mb-2">Tool Calls Log</h3>
          <div className="max-h-64 overflow-auto">
            {toolLog.length === 0 && <div className="text-gray-500">No tool calls yet</div>}
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-600">
                  <th className="p-2">Time</th>
                  <th className="p-2">Tool</th>
                  <th className="p-2">Result</th>
                </tr>
              </thead>
              <tbody>
                {toolLog.map((t, i) => (
                  <tr key={i} className="border-t">
                    <td className="p-2">{t.time}</td>
                    <td className="p-2">{t.tool}</td>
                    <td className="p-2">{String(t.result).slice(0, 80)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="p-4 bg-white rounded shadow">
          <h3 className="font-medium mb-2">State Viewer</h3>
          <pre className="text-xs max-h-64 overflow-auto bg-gray-50 p-2 rounded">{JSON.stringify({ state: 'placeholder' }, null, 2)}</pre>
        </div>
      </section>
    </div>
  )
}

function mockData(): MetricPoint[] {
  const now = Date.now()
  return Array.from({ length: 20 }).map((_, i) => ({ time: new Date(now - (19 - i) * 1000).toLocaleTimeString(), rps: Math.random() * 10, latency: 50 + Math.random() * 200, cost: Math.random() * 2 }))
}
