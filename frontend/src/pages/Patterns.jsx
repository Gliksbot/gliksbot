import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function Patterns() {
  const [patterns, setPatterns] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadPatterns()
  }, [])

  const loadPatterns = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/patterns')
      setPatterns(data?.patterns || [])
    } catch (error) {
      console.error('Failed to load patterns:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Pattern Recognition</h1>
      
      {loading ? (
        <div className="text-center py-8">Loading patterns...</div>
      ) : (
        <div className="space-y-6">
          {/* Pattern Summary */}
          <div className="grid grid-cols-4 gap-4">
            <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40 text-center">
              <div className="text-2xl font-bold text-blue-400">
                {patterns.filter(p => p.type === 'behavioral').length}
              </div>
              <div className="text-sm text-slate-400">Behavioral</div>
            </div>
            <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40 text-center">
              <div className="text-2xl font-bold text-green-400">
                {patterns.filter(p => p.type === 'temporal').length}
              </div>
              <div className="text-sm text-slate-400">Temporal</div>
            </div>
            <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40 text-center">
              <div className="text-2xl font-bold text-purple-400">
                {patterns.filter(p => p.type === 'linguistic').length}
              </div>
              <div className="text-sm text-slate-400">Linguistic</div>
            </div>
            <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40 text-center">
              <div className="text-2xl font-bold text-orange-400">
                {patterns.length}
              </div>
              <div className="text-sm text-slate-400">Total Patterns</div>
            </div>
          </div>

          {/* Pattern List */}
          <div className="space-y-4">
            {patterns.map((pattern, index) => (
              <div key={index} className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-1 rounded text-xs ${
                      pattern.type === 'behavioral' ? 'bg-blue-600' :
                      pattern.type === 'temporal' ? 'bg-green-600' :
                      pattern.type === 'linguistic' ? 'bg-purple-600' :
                      'bg-gray-600'
                    }`}>
                      {pattern.type}
                    </span>
                    <h3 className="font-medium">{pattern.name || `Pattern ${index + 1}`}</h3>
                  </div>
                  <div className="text-sm text-slate-400">
                    Confidence: {((pattern.confidence || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                
                <p className="text-slate-300 mb-3">{pattern.description}</p>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-400">Occurrences:</span> {pattern.count || 0}
                  </div>
                  <div>
                    <span className="text-slate-400">First Seen:</span> {
                      pattern.first_seen ? new Date(pattern.first_seen).toLocaleDateString() : 'Unknown'
                    }
                  </div>
                  <div>
                    <span className="text-slate-400">Last Seen:</span> {
                      pattern.last_seen ? new Date(pattern.last_seen).toLocaleDateString() : 'Unknown'
                    }
                  </div>
                  <div>
                    <span className="text-slate-400">Strength:</span> {
                      pattern.strength ? (pattern.strength * 100).toFixed(1) + '%' : 'N/A'
                    }
                  </div>
                </div>
                
                {pattern.examples && pattern.examples.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-800">
                    <div className="text-sm text-slate-400 mb-2">Examples:</div>
                    <div className="space-y-1">
                      {pattern.examples.slice(0, 3).map((example, idx) => (
                        <div key={idx} className="text-xs text-slate-500 bg-slate-950/60 p-2 rounded">
                          {example}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {patterns.length === 0 && !loading && (
              <div className="text-slate-500 text-center py-8">
                No patterns detected yet. Patterns will be automatically identified as you interact with Dexter.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
