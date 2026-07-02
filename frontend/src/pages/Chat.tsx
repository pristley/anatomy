import React, { useEffect, useRef, useState } from 'react'
import axios from 'axios'

type Message = { id: string; role: 'user' | 'agent'; text: string; time?: string }

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [maxTokens, setMaxTokens] = useState(128)
  const listRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    // fetch recent messages for default agent (mock)
    axios
      .get('/api/chat/recent')
      .then((r) => setMessages(r.data || []))
      .catch(() => setMessages([]))
  }, [])

  useEffect(() => {
    // scroll to bottom on messages change
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }, [messages])

  const send = async () => {
    if (!input.trim()) return
    const msg: Message = { id: String(Date.now()), role: 'user', text: input, time: new Date().toISOString() }
    setMessages((m) => [...m, msg])
    setInput('')
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post('/api/chat/send', { text: msg.text, max_tokens: maxTokens })
      const agentText = res.data?.reply ?? 'no reply'
      setMessages((m) => [...m, { id: String(Date.now() + 1), role: 'agent', text: agentText, time: new Date().toISOString() }])
    } catch (e: any) {
      setError(e?.message || 'send error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 h-full flex flex-col">
      <header className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-semibold">Chat</h1>
        <div className="text-sm text-gray-500">Execution time: 0ms</div>
      </header>

      <div ref={listRef} className="flex-1 overflow-auto p-4 bg-white rounded shadow mb-4">
        {messages.map((m) => (
          <div key={m.id} className={`mb-3 flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'} p-3 rounded max-w-xl`}>
              <div className="text-sm">{m.text}</div>
              <div className="text-xs text-gray-400 mt-1">{new Date(m.time || '').toLocaleTimeString()}</div>
            </div>
          </div>
        ))}
        {loading && <div className="text-sm text-gray-500">Agent is typing...</div>}
        {error && <div className="text-sm text-red-500">{error}</div>}
      </div>

      <div className="bg-white p-4 rounded shadow">
        <div className="flex gap-2 items-center">
          <input
            className="flex-1 border rounded px-3 py-2"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
          />
          <button className="px-4 py-2 bg-green-600 text-white rounded" onClick={send} disabled={loading}>
            Send
          </button>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <label className="text-sm text-gray-600">Max tokens: {maxTokens}</label>
          <input
            type="range"
            min={16}
            max={2048}
            value={maxTokens}
            onChange={(e) => setMaxTokens(Number(e.target.value))}
            className="w-64"
          />
        </div>
      </div>
    </div>
  )
}
