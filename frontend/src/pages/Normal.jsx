import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function Normal() {
  const [request, setRequest] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState('')
  const [history, setHistory] = useState([])

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const { data } = await api.get('/history')
      setHistory(data?.interactions || [])
    } catch (error) {
      console.error('Failed to load history:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!request.trim() || loading) return

    setLoading(true)
    setResponse('')

    try {
      const { data } = await api.post('/chat', {
        message: request,
        mode: 'normal'
      })
      setResponse(data.response)
      setRequest('')
      loadHistory() // Refresh history
    } catch (error) {
      setResponse('Error: ' + (error?.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Normal Mode</h1>
      
      {/* Chat Interface */}
      <div className="space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <textarea
              value={request}
              onChange={(e) => setRequest(e.target.value)}
              placeholder="Enter your request for Dexter..."
              className="w-full h-32 bg-slate-800 border border-slate-700 rounded-lg p-3 resize-none"
              disabled={loading}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !request.trim()}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium"
          >
            {loading ? 'Processing...' : 'Send Request'}
          </button>
        </form>

        {/* Response */}
        {response && (
          <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
            <h3 className="text-lg font-semibold mb-2">Response</h3>
            <div className="whitespace-pre-wrap text-slate-300">{response}</div>
          </div>
        )}

        {/* Recent History */}
        <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
          <h3 className="text-lg font-semibold mb-4">Recent Interactions</h3>
          <div className="space-y-3">
            {history.slice(0, 5).map((interaction, index) => (
              <div key={index} className="border border-slate-800 rounded p-3">
                <div className="text-sm text-slate-400 mb-1">
                  {new Date(interaction.timestamp).toLocaleString()}
                </div>
                <div className="text-slate-300 mb-2">
                  <strong>Request:</strong> {interaction.request}
                </div>
                <div className="text-slate-300">
                  <strong>Response:</strong> {interaction.response?.substring(0, 200)}
                  {interaction.response?.length > 200 && '...'}
                </div>
              </div>
            ))}
            {history.length === 0 && (
              <div className="text-slate-500 text-center py-4">
                No interactions yet. Send your first request to get started.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
