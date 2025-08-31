import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function Models() {
  const [config, setConfig] = useState({})
  const [selectedModel, setSelectedModel] = useState('dexter')
  const [editingModel, setEditingModel] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      setLoading(true)
      setError('')
      const { data } = await api.get('/config')
      setConfig(data || {})
    } catch (error) {
      console.error('Failed to load config:', error)
      setError('Failed to load configuration: ' + (error?.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const saveModelConfig = async (modelName, updatedConfig) => {
    try {
      setSaving(true)
      setError('')
      await api.post(`/models/${modelName}/config`, updatedConfig)
      
      // Update local state
      setConfig(prev => ({
        ...prev,
        models: {
          ...prev.models,
          [modelName]: updatedConfig
        }
      }))
      
      setEditingModel(null)
      alert('Model configuration saved successfully!')
    } catch (error) {
      const errorMsg = error?.response?.data?.detail || error.message
      setError('Failed to save configuration: ' + errorMsg)
      alert('Failed to save: ' + errorMsg)
    } finally {
      setSaving(false)
    }
  }

  const ModelDetailView = ({ modelName, modelConfig }) => {
    const [localConfig, setLocalConfig] = useState(modelConfig || {})

    useEffect(() => {
      setLocalConfig(modelConfig || {})
    }, [modelConfig])

    const updateField = (field, value) => {
      if (field.includes('.')) {
        const [parent, child] = field.split('.')
        setLocalConfig(prev => ({
          ...prev,
          [parent]: {
            ...prev[parent],
            [child]: value
          }
        }))
      } else {
        setLocalConfig(prev => ({
          ...prev,
          [field]: value
        }))
      }
    }

    const getStatus = () => {
      if (!localConfig.enabled) return { status: 'disabled', color: 'yellow', text: 'Disabled' }
      if (!localConfig.provider) return { status: 'error', color: 'red', text: 'No Provider Configured' }
      if (!localConfig.model) return { status: 'error', color: 'red', text: 'No Model Specified' }
      if (!localConfig.endpoint && !localConfig.local_model) return { status: 'error', color: 'red', text: 'No Endpoint URL' }
      if (!localConfig.api_key_env && !localConfig.local_model) return { status: 'error', color: 'red', text: 'Missing API Key Environment Variable' }
      return { status: 'active', color: 'green', text: 'Ready' }
    }

    const status = getStatus()

    return (
      <div className="border border-slate-600 rounded-lg p-6 bg-slate-800/50">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold capitalize">{modelName}</h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium bg-${status.color}-600/20 text-${status.color}-400 border border-${status.color}-600/30`}>
              {status.text}
            </span>
          </div>
          <div className="flex gap-2">
            {editingModel === modelName ? (
              <>
                <button
                  onClick={() => saveModelConfig(modelName, localConfig)}
                  disabled={saving}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg font-medium text-sm"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={() => {
                    setEditingModel(null)
                    setLocalConfig(modelConfig || {})
                  }}
                  className="px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg font-medium text-sm"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                onClick={() => setEditingModel(modelName)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium text-sm"
              >
                Edit
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Basic Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-300 border-b border-slate-600 pb-2">Basic Configuration</h3>
            
            <div>
              <label className="block text-sm font-medium mb-2">Enabled</label>
              <select
                value={localConfig.enabled ? 'true' : 'false'}
                onChange={(e) => updateField('enabled', e.target.value === 'true')}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              >
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Provider</label>
              <select
                value={localConfig.provider || ''}
                onChange={(e) => updateField('provider', e.target.value)}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              >
                <option value="">Select Provider</option>
                <option value="openai">OpenAI</option>
                <option value="ollama">Ollama</option>
                <option value="anthropic">Anthropic</option>
                <option value="OpenAI">OpenAI Compatible</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <input
                type="text"
                value={localConfig.model || ''}
                onChange={(e) => updateField('model', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="e.g., gpt-4o, llama3.1:8b"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Endpoint</label>
              <input
                type="text"
                value={localConfig.endpoint || ''}
                onChange={(e) => updateField('endpoint', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="e.g., https://api.openai.com/v1"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">API Key Environment Variable</label>
              <input
                type="text"
                value={localConfig.api_key_env || ''}
                onChange={(e) => updateField('api_key_env', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="e.g., OPENAI_API_KEY"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Local Model</label>
              <select
                value={localConfig.local_model ? 'true' : 'false'}
                onChange={(e) => updateField('local_model', e.target.value === 'true')}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              >
                <option value="false">Remote API</option>
                <option value="true">Local Model</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Local Endpoint</label>
              <input
                type="text"
                value={localConfig.local_endpoint || 'http://localhost:11434'}
                onChange={(e) => updateField('local_endpoint', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="http://localhost:11434"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
          </div>

          {/* AI Configuration */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-300 border-b border-slate-600 pb-2">AI Configuration</h3>
            
            <div>
              <label className="block text-sm font-medium mb-2">Role</label>
              <input
                type="text"
                value={localConfig.role || ''}
                onChange={(e) => updateField('role', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="e.g., Chief Orchestrator"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Identity</label>
              <textarea
                value={localConfig.identity || ''}
                onChange={(e) => updateField('identity', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="Describe the AI's identity and core characteristics..."
                rows={3}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">System Prompt</label>
              <textarea
                value={localConfig.prompt || ''}
                onChange={(e) => updateField('prompt', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="Enter the system prompt that defines the AI's behavior..."
                rows={4}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Collaboration Enabled</label>
              <select
                value={localConfig.collaboration_enabled ? 'true' : 'false'}
                onChange={(e) => updateField('collaboration_enabled', e.target.value === 'true')}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              >
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Collaboration Directory</label>
              <input
                type="text"
                value={localConfig.collaboration_directory || ''}
                onChange={(e) => updateField('collaboration_directory', e.target.value)}
                disabled={editingModel !== modelName}
                placeholder="./collaboration/modelname"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
          </div>
        </div>

        {/* Parameters Section */}
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-slate-300 border-b border-slate-600 pb-2 mb-4">Model Parameters</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Temperature</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={localConfig.params?.temperature || 0.7}
                onChange={(e) => updateField('params.temperature', parseFloat(e.target.value) || 0)}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Top P</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={localConfig.params?.top_p || 0.9}
                onChange={(e) => updateField('params.top_p', parseFloat(e.target.value) || 0)}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Max Tokens</label>
              <input
                type="number"
                min="1"
                value={localConfig.params?.max_tokens || 2048}
                onChange={(e) => updateField('params.max_tokens', parseInt(e.target.value) || 0)}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Context Length</label>
              <input
                type="number"
                min="1"
                value={localConfig.params?.num_ctx || localConfig.params?.context_length || 4096}
                onChange={(e) => updateField('params.num_ctx', parseInt(e.target.value) || 0)}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Frequency Penalty</label>
              <input
                type="number"
                step="0.1"
                min="-2"
                max="2"
                value={localConfig.params?.frequency_penalty || 0}
                onChange={(e) => updateField('params.frequency_penalty', parseFloat(e.target.value) || 0)}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Presence Penalty</label>
              <input
                type="number"
                step="0.1"
                min="-2"
                max="2"
                value={localConfig.params?.presence_penalty || 0}
                onChange={(e) => updateField('params.presence_penalty', parseFloat(e.target.value) || 0)}
                disabled={editingModel !== modelName}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2 disabled:opacity-50"
              />
            </div>
          </div>
        </div>
      </div>
    )
  }

  const models = config.models || {}

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Model Configuration</h1>
        <button
          onClick={loadConfig}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg font-medium"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-900/50 border border-red-600 rounded-lg text-red-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <div className="text-slate-400">Loading model configuration...</div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Model Selector */}
          <div className="bg-slate-800/30 rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-3">Available Models</h2>
            <div className="flex flex-wrap gap-2">
              {Object.keys(models).map((modelName) => {
                const model = models[modelName]
                const isActive = model?.enabled
                return (
                  <button
                    key={modelName}
                    onClick={() => setSelectedModel(modelName)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      selectedModel === modelName
                        ? 'bg-blue-600 text-white'
                        : isActive
                        ? 'bg-green-600/20 text-green-400 hover:bg-green-600/30'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    <span className="capitalize">{modelName}</span>
                    {isActive && <span className="ml-2 text-xs">●</span>}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Selected Model Detail */}
          {selectedModel && models[selectedModel] && (
            <ModelDetailView
              modelName={selectedModel}
              modelConfig={models[selectedModel]}
            />
          )}

          {/* Voting Weights */}
          <div className="bg-slate-800/30 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Voting Weights</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(config.voting?.weights || {}).map(([model, weight]) => (
                <div key={model} className="text-center">
                  <div className="text-sm text-slate-400 capitalize">{model}</div>
                  <div className="text-lg font-semibold">{(weight * 100).toFixed(0)}%</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
