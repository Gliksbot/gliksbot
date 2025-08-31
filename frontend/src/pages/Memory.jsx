import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function Memory() {
  const [memories, setMemories] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadMemories()
  }, [])

  const loadMemories = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/memory')
      setMemories(data?.memories || [])
    } catch (error) {
      console.error('Failed to load memories:', error)
    } finally {
      setLoading(false)
    }
  }

  const searchMemories = async () => {
    if (!searchTerm.trim()) {
      loadMemories()
      return
    }

    try {
      setLoading(true)
      const { data } = await api.get(`/memory/search?q=${encodeURIComponent(searchTerm)}`)
      setMemories(data?.results || [])
    } catch (error) {
      console.error('Failed to search memories:', error)
    } finally {
      setLoading(false)
    }
  }

  const clearMemory = async () => {
    if (!confirm('Are you sure you want to clear all memories? This cannot be undone.')) {
      return
    }

    try {
      await api.delete('/memory')
      setMemories([])
      alert('Memory cleared successfully')
    } catch (error) {
      alert('Failed to clear memory: ' + (error?.response?.data?.detail || error.message))
    }
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Memory System</h1>
        <button
          onClick={clearMemory}
          className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium"
        >
          Clear All Memory
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search memories..."
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2"
            onKeyPress={(e) => e.key === 'Enter' && searchMemories()}
          />
          <button
            onClick={searchMemories}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg font-medium"
          >
            Search
          </button>
          <button
            onClick={loadMemories}
            className="px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg font-medium"
          >
            Show All
          </button>
        </div>
      </div>

      {/* Memory List */}
      {loading ? (
        <div className="text-center py-8">Loading memories...</div>
      ) : (
        <div className="space-y-4">
          {memories.map((memory, index) => (
            <div key={index} className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs ${
                    memory.type === 'ltm' ? 'bg-blue-600' : 'bg-green-600'
                  }`}>
                    {memory.type?.toUpperCase()}
                  </span>
                  {memory.timestamp && (
                    <span className="text-xs text-slate-400">
                      {new Date(memory.timestamp).toLocaleString()}
                    </span>
                  )}
                </div>
                {memory.score && (
                  <span className="text-xs text-slate-400">
                    Score: {memory.score.toFixed(3)}
                  </span>
                )}
              </div>
              
              <div className="text-slate-300 whitespace-pre-wrap">
                {memory.content || memory.text}
              </div>
              
              {memory.metadata && (
                <div className="mt-2 pt-2 border-t border-slate-800">
                  <div className="text-xs text-slate-500">
                    Metadata: {JSON.stringify(memory.metadata)}
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {memories.length === 0 && !loading && (
            <div className="text-slate-500 text-center py-8">
              {searchTerm ? 'No memories found matching your search.' : 'No memories stored yet.'}
            </div>
          )}
        </div>
      )}

      {/* Memory Stats */}
      <div className="mt-8 grid grid-cols-3 gap-4">
        <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40 text-center">
          <div className="text-2xl font-bold text-blue-400">
            {memories.filter(m => m.type === 'ltm').length}
          </div>
          <div className="text-sm text-slate-400">Long-term Memories</div>
        </div>
        <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40 text-center">
          <div className="text-2xl font-bold text-green-400">
            {memories.filter(m => m.type === 'stm').length}
          </div>
          <div className="text-sm text-slate-400">Short-term Memories</div>
        </div>
        <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40 text-center">
          <div className="text-2xl font-bold text-purple-400">
            {memories.length}
          </div>
          <div className="text-sm text-slate-400">Total Memories</div>
        </div>
      </div>
    </div>
  )
}
