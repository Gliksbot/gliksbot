import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function ConfigPage() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [configText, setConfigText] = useState('')

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/config')
      setConfig(data)
      setConfigText(JSON.stringify(data, null, 2))
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    try {
      setSaving(true)
      const parsedConfig = JSON.parse(configText)
      await api.post('/config', parsedConfig)
      setConfig(parsedConfig)
      alert('Configuration saved successfully!')
    } catch (error) {
      if (error instanceof SyntaxError) {
        alert('Invalid JSON format. Please check your syntax.')
      } else {
        alert('Failed to save config: ' + (error?.response?.data?.detail || error.message))
      }
    } finally {
      setSaving(false)
    }
  }

  const resetConfig = () => {
    if (confirm('Are you sure you want to reset to the loaded configuration? Unsaved changes will be lost.')) {
      setConfigText(JSON.stringify(config, null, 2))
    }
  }

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Configuration</h1>
        <div className="flex gap-2">
          <button
            onClick={resetConfig}
            className="px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg text-sm font-medium"
          >
            Reset
          </button>
          <button
            onClick={saveConfig}
            disabled={saving}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-sm font-medium"
          >
            {saving ? 'Saving...' : 'Save Config'}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading configuration...</div>
      ) : (
        <div className="space-y-6">
          {/* Config Editor */}
          <div className="border border-slate-700 rounded-lg bg-slate-900/40">
            <div className="border-b border-slate-700 p-3">
              <h3 className="font-medium">config.json</h3>
            </div>
            <div className="p-0">
              <textarea
                value={configText}
                onChange={(e) => setConfigText(e.target.value)}
                className="w-full h-96 bg-transparent border-0 p-4 font-mono text-sm resize-none focus:outline-none"
                placeholder="Loading configuration..."
              />
            </div>
          </div>

          {/* Quick Config Summary */}
          {config && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
                <h3 className="font-medium mb-3">Models</h3>
                <div className="space-y-2">
                  {Object.entries(config.models || {}).map(([name, model]) => (
                    <div key={name} className="flex items-center justify-between text-sm">
                      <span>{name}</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        model.enabled ? 'bg-green-600' : 'bg-gray-600'
                      }`}>
                        {model.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
                <h3 className="font-medium mb-3">System Settings</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Database:</span>
                    <span className="text-slate-400">{config.runtime?.db_path || 'Default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>FTS Enabled:</span>
                    <span className={config.runtime?.enable_fts ? 'text-green-400' : 'text-red-400'}>
                      {config.runtime?.enable_fts ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Campaigns:</span>
                    <span className={config.campaigns?.enabled ? 'text-green-400' : 'text-red-400'}>
                      {config.campaigns?.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
                <h3 className="font-medium mb-3">Sandbox & Security</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Provider:</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      config.runtime?.sandbox?.provider === 'docker' ? 'bg-blue-600' : 
                      config.runtime?.sandbox?.provider === 'hyperv' ? 'bg-purple-600' : 'bg-gray-600'
                    }`}>
                      {config.runtime?.sandbox?.provider || 'None'}
                    </span>
                  </div>
                  {config.runtime?.sandbox?.provider === 'docker' && (
                    <>
                      <div className="flex justify-between">
                        <span>Docker Image:</span>
                        <span className="text-slate-400 text-xs">
                          {config.runtime?.sandbox?.docker?.image || 'python:3.11-slim'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Memory Limit:</span>
                        <span className="text-slate-400">
                          {config.runtime?.sandbox?.docker?.memory_limit || '256m'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Network:</span>
                        <span className="text-slate-400">
                          {config.runtime?.sandbox?.docker?.network_mode || 'none'}
                        </span>
                      </div>
                    </>
                  )}
                  {config.runtime?.sandbox?.provider === 'hyperv' && (
                    <div className="flex justify-between">
                      <span>VM Name:</span>
                      <span className="text-slate-400">
                        {config.runtime?.sandbox?.hyperv?.vm_name || 'DexterVM'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Configuration Help */}
          <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
            <h3 className="font-medium mb-3">Configuration Help</h3>
            <div className="text-sm text-slate-400 space-y-2">
              <p>• <strong>models</strong>: Configure LLM providers and their settings</p>
              <p>• <strong>runtime.sandbox.provider</strong>: Choose 'docker' (recommended) or 'hyperv' for code execution</p>
              <p>• <strong>runtime.sandbox.docker</strong>: Configure Docker container settings for secure code execution</p>
              <p>• <strong>campaigns</strong>: Enable/disable campaign mode and set limits</p>
              <p>• <strong>voting</strong>: Set voting weights for LLM collaboration</p>
              <p>• <strong>domain</strong>: Configure domain settings and CORS</p>
              <p>• Always backup before making changes!</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
