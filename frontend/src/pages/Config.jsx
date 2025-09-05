import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function ConfigPage() {
  // Core state
  const [cfg, setCfg] = useState(null)            // Unwrapped config object (data.config)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [rawText, setRawText] = useState('')      // Raw JSON editor text
  const [sandboxUpdating, setSandboxUpdating] = useState(false)
  const [envEdits, setEnvEdits] = useState({})    // Local edits for api_key_env per model
  const [message, setMessage] = useState(null)

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/config')
      const inner = data.config || {}
      setCfg(inner)
      setRawText(JSON.stringify(inner, null, 2))
      // Prime env edits
      const envMap = {}
      Object.entries(inner.models || {}).forEach(([name, m]) => { envMap[name] = m.api_key_env || '' })
      setEnvEdits(envMap)
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to load config: ' + (e?.response?.data?.detail || e.message) })
    } finally { setLoading(false) }
  }

  const saveRaw = async () => {
    try {
      setSaving(true)
      const parsed = JSON.parse(rawText)
      await api.put('/config', parsed)
      setCfg(parsed)
      setMessage({ type: 'success', text: 'Configuration saved' })
    } catch (e) {
      if (e instanceof SyntaxError) {
        setMessage({ type: 'error', text: 'Invalid JSON syntax' })
      } else {
        setMessage({ type: 'error', text: 'Save failed: ' + (e?.response?.data?.detail || e.message) })
      }
    } finally { setSaving(false) }
  }

  const resetRaw = () => { if (cfg) setRawText(JSON.stringify(cfg, null, 2)) }

  // Sandbox controls
  const currentProvider = cfg?.runtime?.sandbox?.provider || 'docker'
  const autoPromote = cfg?.runtime?.sandbox?.auto_promote_skills !== false // default true

  const updateSandbox = async (updates) => {
    setSandboxUpdating(true)
    try {
      await api.post('/sandbox/settings', updates)
      await load()
      setMessage({ type: 'success', text: 'Sandbox settings updated' })
    } catch (e) {
      setMessage({ type: 'error', text: 'Sandbox update failed: ' + (e?.response?.data?.detail || e.message) })
    } finally { setSandboxUpdating(false) }
  }

  const onProviderChange = (e) => updateSandbox({ provider: e.target.value })
  const toggleAutoPromote = () => updateSandbox({ auto_promote: !autoPromote })

  // Update model api_key_env (name only; value must be set in host environment)
  const saveModelEnv = async (modelName) => {
    try {
      const model = { ...(cfg.models?.[modelName] || {}) }
      model.api_key_env = envEdits[modelName] || ''
      await api.post(`/models/${modelName}/config`, model)
      setMessage({ type: 'success', text: `Updated ${modelName} api_key_env` })
      await load()
    } catch (e) {
      setMessage({ type: 'error', text: `Failed updating ${modelName}: ` + (e?.response?.data?.detail || e.message) })
    }
  }

  const updateDockerField = (field, value) => {
    setCfg(prev => {
      const next = { ...prev }
      next.runtime = next.runtime || {}
      next.runtime.sandbox = next.runtime.sandbox || {}
      next.runtime.sandbox.docker = next.runtime.sandbox.docker || {}
      next.runtime.sandbox.docker[field] = value
      setRawText(JSON.stringify(next, null, 2))
      return next
    })
  }
  const updateHypervField = (field, value) => {
    setCfg(prev => {
      const next = { ...prev }
      next.runtime = next.runtime || {}
      next.runtime.sandbox = next.runtime.sandbox || {}
      next.runtime.sandbox.hyperv = next.runtime.sandbox.hyperv || {}
      next.runtime.sandbox.hyperv[field] = value
      setRawText(JSON.stringify(next, null, 2))
      return next
    })
  }

  return (
    <div className="p-4 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Configuration</h1>
        <div className="flex gap-2">
          <button onClick={resetRaw} className="px-3 py-2 bg-slate-600 hover:bg-slate-500 rounded text-sm">Reset</button>
          <button onClick={saveRaw} disabled={saving} className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-sm">{saving ? 'Saving...' : 'Save Raw JSON'}</button>
        </div>
      </div>

      {message && (
        <div className={`p-3 text-sm rounded border ${message.type === 'error' ? 'bg-red-900/40 border-red-600 text-red-200' : 'bg-emerald-900/40 border-emerald-600 text-emerald-200'}`}>{message.text}</div>
      )}

      {loading && <div className="py-8 text-center">Loading...</div>}

      {!loading && cfg && (
        <>
          {/* Sandbox Controls */}
          <div className="border border-slate-700 rounded-lg bg-slate-900/40">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h2 className="font-semibold">Sandbox & Skill Promotion</h2>
              <div className="flex items-center gap-3">
                <label className="text-sm flex items-center gap-2">Provider:
                  <select disabled={sandboxUpdating} value={currentProvider} onChange={onProviderChange} className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-sm">
                    <option value="docker">docker</option>
                    <option value="hyperv">hyperv</option>
                  </select>
                </label>
                <button onClick={toggleAutoPromote} disabled={sandboxUpdating} className={`px-3 py-1 rounded text-sm ${autoPromote ? 'bg-emerald-600' : 'bg-slate-600'}`}>{autoPromote ? 'Auto-Promote ON' : 'Auto-Promote OFF'}</button>
              </div>
            </div>
            <div className="p-4 grid md:grid-cols-2 gap-6 text-sm">
              {/* Docker Settings */}
              <div>
                <h3 className="font-medium mb-2">Docker Settings</h3>
                <div className="space-y-2">
                  {['image','memory_limit','cpu_limit','timeout_sec','network_mode'].map(field => (
                    <div key={field} className="flex items-center gap-2">
                      <label className="w-32 capitalize">{field.replace('_',' ')}</label>
                      <input
                        value={cfg.runtime?.sandbox?.docker?.[field] ?? ''}
                        onChange={e => updateDockerField(field, e.target.value)}
                        className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-1"
                        placeholder={`docker ${field}`}
                      />
                    </div>
                  ))}
                  <p className="text-xs text-slate-400">Edit values then click Save Raw JSON to persist.</p>
                </div>
              </div>
              {/* Hyper-V Settings */}
              <div>
                <h3 className="font-medium mb-2">Hyper-V Settings</h3>
                <div className="space-y-2">
                  {['vm_name','vm_user','vm_password_env','vm_shared_dir','python_exe','timeout_sec'].map(field => (
                    <div key={field} className="flex items-center gap-2">
                      <label className="w-40 capitalize">{field.replace('_',' ')}</label>
                      <input
                        value={cfg.runtime?.sandbox?.hyperv?.[field] ?? ''}
                        onChange={e => updateHypervField(field, e.target.value)}
                        className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-1"
                        placeholder={`hyperv ${field}`}
                      />
                    </div>
                  ))}
                  <p className="text-xs text-slate-400">Set vm_password_env to the NAME of the env var (value stays outside config).</p>
                </div>
              </div>
            </div>
          </div>

          {/* Model API Key Env Mapping */}
          <div className="border border-slate-700 rounded-lg bg-slate-900/40">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h2 className="font-semibold">Model Environment Variables</h2>
              <span className="text-xs text-slate-400">(Only names stored; values must be exported on host)</span>
            </div>
            <div className="p-4 space-y-3 text-sm">
              {Object.entries(cfg.models || {}).map(([name, m]) => (
                <div key={name} className="flex flex-wrap items-center gap-2 border border-slate-700/50 rounded px-3 py-2">
                  <span className="font-mono text-slate-300 w-32 truncate">{name}</span>
                  <input
                    value={envEdits[name] ?? ''}
                    onChange={e => setEnvEdits(prev => ({ ...prev, [name]: e.target.value }))
                    }
                    placeholder="API key env variable"
                    className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-1"
                  />
                  <button onClick={() => saveModelEnv(name)} className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-xs">Save</button>
                  <span className={`text-xs px-2 py-0.5 rounded ${m.enabled ? 'bg-emerald-600' : 'bg-slate-600'}`}>{m.enabled ? 'ENABLED' : 'DISABLED'}</span>
                  {m.local_model && <span className="text-xs bg-indigo-600 px-2 py-0.5 rounded">LOCAL</span>}
                </div>
              ))}
              {Object.keys(cfg.models || {}).length === 0 && (
                <div className="text-slate-500 text-sm">No models configured.</div>
              )}
            </div>
          </div>

          {/* Raw JSON Editor */}
          <div className="border border-slate-700 rounded-lg bg-slate-900/40">
            <div className="p-3 border-b border-slate-700 flex items-center justify-between">
              <h2 className="font-semibold">Raw config.json Editor</h2>
              <span className="text-xs text-slate-400">Advanced edits only. Avoid pasting secrets.</span>
            </div>
            <textarea
              value={rawText}
              onChange={e => setRawText(e.target.value)}
              className="w-full h-80 bg-transparent p-4 font-mono text-xs resize-none focus:outline-none"
              spellCheck={false}
            />
          </div>

          {/* Help Section */}
          <div className="border border-slate-700 rounded-lg bg-slate-900/40 p-4 text-sm text-slate-300 space-y-2">
            <h3 className="font-medium">Guidance</h3>
            <ul className="list-disc ml-5 space-y-1">
              <li>Switch sandbox provider between Docker (cross-platform) and Hyper-V (Windows only).</li>
              <li>Auto-Promote controls whether validated skills are added without review.</li>
              <li>Only store environment variable NAMES (api_key_env, vm_password_env), never secret values.</li>
              <li>After changing provider or key names, restart backend or ensure env variables are exported.</li>
              <li>Use Raw JSON editor for advanced fields (voting weights, collaboration settings, etc.).</li>
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
