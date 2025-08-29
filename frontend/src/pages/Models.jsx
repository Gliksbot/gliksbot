import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function Models() {
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadModels()
  }, [])

  const loadModels = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/models')
      setModels(data?.models || [])
    } catch (error) {
      console.error('Failed to load models:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleModel = async (modelName) => {
    try {
      const model = models.find(m => m.name === modelName)
      const newEnabled = !model.enabled
      
      await api.post(`/models/${modelName}/toggle`, { enabled: newEnabled })
      
      setModels(prev => prev.map(m => 
        m.name === modelName ? { ...m, enabled: newEnabled } : m
      ))
    } catch (error) {
      alert('Failed to toggle model: ' + (error?.response?.data?.detail || error.message))
    }
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Model Configuration</h1>
      
      {loading ? (
        <div className="text-center py-8">Loading models...</div>
      ) : (
        <div className="space-y-4">
          {models.map((model) => (
            <div key={model.name} className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-semibold">{model.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs ${
                    model.enabled ? 'bg-green-600' : 'bg-gray-600'
                  }`}>
                    {model.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                  <span className="px-2 py-1 rounded text-xs bg-blue-600">
                    {model.role}
                  </span>
                </div>
                <button
                  onClick={() => toggleModel(model.name)}
                  className={`px-3 py-1 rounded text-sm ${
                    model.enabled 
                      ? 'bg-red-600 hover:bg-red-500' 
                      : 'bg-green-600 hover:bg-green-500'
                  }`}
                >
                  {model.enabled ? 'Disable' : 'Enable'}
                </button>
              </div>
              
              <p className="text-slate-300 mb-3">{model.identity}</p>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-slate-400">Provider:</span> {model.provider}
                </div>
                <div>
                  <span className="text-slate-400">Model:</span> {model.model}
                </div>
                {model.endpoint && (
                  <div>
                    <span className="text-slate-400">Endpoint:</span> {model.endpoint}
                  </div>
                )}
                {model.params && (
                  <div>
                    <span className="text-slate-400">Temperature:</span> {model.params.temperature}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {models.length === 0 && (
            <div className="text-slate-500 text-center py-8">
              No models configured. Check your config.json file.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
