import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

export default function useWebSocket<T = any>(opts: { url?: string; pollUrl?: string; pollIntervalMs?: number }) {
  const { url, pollUrl = '/api/monitoring', pollIntervalMs = 5000 } = opts
  const wsRef = useRef<WebSocket | null>(null)
  const [data, setData] = useState<T | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!url) return
    try {
      const ws = new WebSocket(url)
      wsRef.current = ws
      ws.onopen = () => setConnected(true)
      ws.onmessage = (ev) => {
        try {
          setData(JSON.parse(ev.data))
        } catch {
          setData(ev.data as any)
        }
      }
      ws.onclose = () => setConnected(false)
      ws.onerror = () => setConnected(false)
      return () => ws.close()
    } catch {
      setConnected(false)
    }
  }, [url])

  // polling fallback
  useEffect(() => {
    if (url) return
    let mounted = true
    const fetcher = () => {
      axios
        .get(pollUrl)
        .then((r) => mounted && setData(r.data))
        .catch(() => {})
    }
    fetcher()
    const t = setInterval(fetcher, pollIntervalMs)
    return () => {
      mounted = false
      clearInterval(t)
    }
  }, [url, pollUrl, pollIntervalMs])

  return { data, connected }
}
