import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function Models() {
  const [slots, setSlots] = useState({})
  const [selectedSlot, setSelectedSlot] = useState('dexter')
  const [selectedParameter, setSelectedParameter] = useState('provider')
  const [parameterValue, setParameterValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const slotOptions = [
    { value: 'dexter', label: 'Dexter (Main)' },
    { value: 'slot_1', label: 'Slot 1' },
    { value: 'slot_2', label: 'Slot 2' },
    { value: 'slot_3', label: 'Slot 3' },
    { value: 'slot_4', label: 'Slot 4' },
    { value: 'slot_5', label: 'Slot 5' }
  ]

  const parameterOptions = [
    { value: 'provider', label: 'Provider' },
    { value: 'endpoint', label: 'Endpoint/Host URL' },
    { value: 'api_key', label: 'API Key' },
    { value: 'model', label: 'Model' },
    { value: 'identity', label: 'Identity' },
    { value: 'role', label: 'Role' },
    { value: 'prompt', label: 'System Prompt' },
    { value: 'temperature', label: 'Temperature' },
    { value: 'enabled', label: 'Enabled' }
  ]

  useEffect(() => {
    loadSlots()
  }, [])

  useEffect(() => {
    // Update parameter value when slot or parameter changes
    const currentSlot = slots[selectedSlot]
    if (currentSlot) {
      if (selectedParameter === 'temperature') {
        setParameterValue(currentSlot.params?.temperature?.toString() || '0.7')
      } else if (selectedParameter === 'enabled') {
        setParameterValue(currentSlot.enabled ? 'true' : 'false')
      } else {
        setParameterValue(currentSlot[selectedParameter] || '')
      }
    } else {
      setParameterValue('')
    }
  }, [selectedSlot, selectedParameter, slots])

  const loadSlots = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/models')
      
      // Transform the response into slot format
      const slotsData = {}
      if (data?.models) {
        data.models.forEach(model => {
          slotsData[model.name] = model
        })
      }
      
      setSlots(slotsData)
    } catch (error) {
      console.error('Failed to load slots:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveParameter = async () => {
    if (!parameterValue.trim() && selectedParameter !== 'enabled') return

    setSaving(true)
    try {
      let value = parameterValue
      
      if (selectedParameter === 'enabled') {
        value = value === 'true'
      } else if (selectedParameter === 'temperature') {
        value = parseFloat(value) || 0.7
      }

      await api.post(`/models/${selectedSlot}/config`, {
        parameter: selectedParameter,
        value: value
      })
      
      // Update local state
      setSlots(prev => ({
        ...prev,
        [selectedSlot]: {
          ...prev[selectedSlot],
          [selectedParameter]: selectedParameter === 'temperature' 
            ? { ...prev[selectedSlot]?.params, temperature: value }
            : value
        }
      }))

      alert('Parameter saved successfully!')
      
    } catch (error) {
      alert('Failed to save parameter: ' + (error?.response?.data?.detail || error.message))
    } finally {
      setSaving(false)
    }
  }

  const getSlotStatus = (slotData) => {
    if (!slotData) return { status: 'not-configured', message: 'Not configured' }
    if (!slotData.enabled) return { status: 'disabled', message: 'Disabled' }
    if (!slotData.api_key) return { status: 'error', message: 'Missing API key' }
    if (!slotData.provider) return { status: 'error', message: 'Missing provider' }
    if (!slotData.model) return { status: 'error', message: 'Missing model' }
    return { status: 'active', message: 'Active' }
  }

  const currentSlot = slots[selectedSlot]
  const slotStatus = getSlotStatus(currentSlot)

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Model Configuration</h1>
      
      {loading ? (
        <div className="text-center py-8">Loading model slots...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Configuration Panel */}
          <div className="space-y-6">
            <div className="border border-slate-700 rounded-lg p-6 bg-slate-900/40">
              <h2 className="text-lg font-semibold mb-4">Quick Configuration</h2>
              
              {/* Slot Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Select Slot:</label>
                <select
                  value={selectedSlot}
                  onChange={(e) => setSelectedSlot(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3"
                >
                  {slotOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Parameter Selector */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Select Parameter:</label>
                <select
                  value={selectedParameter}
                  onChange={(e) => setSelectedParameter(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3"
                >
                  {parameterOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Parameter Value Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Value:</label>
                {selectedParameter === 'enabled' ? (
                  <select
                    value={parameterValue}
                    onChange={(e) => setParameterValue(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3"
                  >
                    <option value="false">Disabled</option>
                    <option value="true">Enabled</option>
                  </select>
                ) : selectedParameter === 'prompt' ? (
                  <textarea
                    value={parameterValue}
                    onChange={(e) => setParameterValue(e.target.value)}
                    placeholder={`Enter ${selectedParameter}...`}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 h-32 resize-none"
                  />
                ) : (
                  <input
                    type={selectedParameter === 'temperature' ? 'number' : 'text'}
                    step={selectedParameter === 'temperature' ? '0.1' : undefined}
                    min={selectedParameter === 'temperature' ? '0' : undefined}
                    max={selectedParameter === 'temperature' ? '2' : undefined}
                    value={parameterValue}
                    onChange={(e) => setParameterValue(e.target.value)}
                    placeholder={`Enter ${selectedParameter}...`}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3"
                  />
                )}
              </div>

              <button
                onClick={saveParameter}
                disabled={saving || (!parameterValue.trim() && selectedParameter !== 'enabled')}
                className="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium"
              >
                {saving ? 'Saving...' : 'Save Parameter'}
              </button>
            </div>
          </div>

          {/* Slots Overview */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Slots Overview</h2>
            
            {slotOptions.map(({ value, label }) => {
              const slotData = slots[value]
              const status = getSlotStatus(slotData)
              
              return (
                <div 
                  key={value}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    selectedSlot === value 
                      ? 'border-emerald-500 bg-emerald-900/20' 
                      : 'border-slate-700 bg-slate-900/40 hover:bg-slate-800/40'
                  }`}
                  onClick={() => setSelectedSlot(value)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{label}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${
                      status.status === 'active' ? 'bg-green-600' :
                      status.status === 'error' ? 'bg-red-600' :
                      status.status === 'disabled' ? 'bg-yellow-600' :
                      'bg-gray-600'
                    }`}>
                      {status.message}
                    </span>
                  </div>
                  
                  {slotData && (
                    <div className="text-sm text-slate-400 space-y-1">
                      <div>Provider: {slotData.provider || 'Not set'}</div>
                      <div>Model: {slotData.model || 'Not set'}</div>
                      <div>Role: {slotData.role || 'Not set'}</div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
