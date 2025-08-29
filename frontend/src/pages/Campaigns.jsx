import React, { useState, useEffect } from 'react'
import { api } from '../api'

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState([])
  const [selectedCampaign, setSelectedCampaign] = useState(null)
  const [newCampaignName, setNewCampaignName] = useState('')
  const [newCampaignDesc, setNewCampaignDesc] = useState('')
  const [newCampaignRequest, setNewCampaignRequest] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadCampaigns()
    const interval = setInterval(loadCampaigns, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const loadCampaigns = async () => {
    try {
      const { data } = await api.get('/campaigns')
      setCampaigns(data || [])
    } catch (error) {
      console.error('Failed to load campaigns:', error)
    }
  }

  const createCampaign = async () => {
    if (!newCampaignName.trim()) return
    
    setLoading(true)
    try {
      const { data } = await api.post('/campaigns', {
        name: newCampaignName,
        description: newCampaignDesc,
        initial_request: newCampaignRequest
      })
      setCampaigns(prev => [data, ...prev])
      setNewCampaignName('')
      setNewCampaignDesc('')
      setNewCampaignRequest('')
      setShowCreateForm(false)
      setSelectedCampaign(data)
    } catch (error) {
      alert('Failed to create campaign: ' + (error?.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'paused': return 'bg-yellow-500'
      case 'completed': return 'bg-blue-500'
      case 'failed': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  const getObjectiveStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400'
      case 'in_progress': return 'text-yellow-400'
      case 'failed': return 'text-red-400'
      default: return 'text-slate-400'
    }
  }

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Campaign Mode</h1>
        <button 
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-sm font-medium"
        >
          New Campaign
        </button>
      </div>

      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Create New Campaign</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Campaign name..."
                value={newCampaignName}
                onChange={(e) => setNewCampaignName(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
              />
              <textarea
                placeholder="Campaign description..."
                value={newCampaignDesc}
                onChange={(e) => setNewCampaignDesc(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 h-20"
              />
              <textarea
                placeholder="Initial request (e.g., 'Generate me some income')..."
                value={newCampaignRequest}
                onChange={(e) => setNewCampaignRequest(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 h-20"
              />
              <div className="flex gap-2">
                <button
                  onClick={createCampaign}
                  disabled={loading || !newCampaignName.trim()}
                  className="flex-1 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-sm"
                >
                  {loading ? 'Creating...' : 'Create Campaign'}
                </button>
                <button
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Campaign List */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Active Campaigns</h2>
          <div className="space-y-2">
            {campaigns.map((campaign) => (
              <div
                key={campaign.id}
                onClick={() => setSelectedCampaign(campaign)}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedCampaign?.id === campaign.id 
                    ? 'border-emerald-500 bg-emerald-500/10' 
                    : 'border-slate-700 bg-slate-900/40 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(campaign.status)}`} />
                  <h3 className="font-medium truncate">{campaign.name}</h3>
                </div>
                <p className="text-sm text-slate-400 mb-2 line-clamp-2">{campaign.description}</p>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>{campaign.objectives?.length || 0} objectives</span>
                  <span>{campaign.skills_generated?.length || 0} skills</span>
                  <span>{Math.round((campaign.progress?.overall || 0) * 100)}%</span>
                </div>
              </div>
            ))}
            {campaigns.length === 0 && (
              <div className="text-slate-500 text-center py-8">
                No campaigns yet. Create your first campaign to get started.
              </div>
            )}
          </div>
        </div>

        {/* Campaign Details */}
        <div className="lg:col-span-2">
          {selectedCampaign ? (
            <div className="space-y-6">
              {/* Campaign Header */}
              <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(selectedCampaign.status)}`} />
                  <h2 className="text-xl font-semibold">{selectedCampaign.name}</h2>
                </div>
                <p className="text-slate-300 mb-4">{selectedCampaign.description}</p>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-emerald-400">
                      {Math.round((selectedCampaign.progress?.overall || 0) * 100)}%
                    </div>
                    <div className="text-sm text-slate-400">Overall Progress</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">
                      {selectedCampaign.progress?.objectives_completed || 0}
                    </div>
                    <div className="text-sm text-slate-400">Objectives Done</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">
                      {selectedCampaign.progress?.skills_created || 0}
                    </div>
                    <div className="text-sm text-slate-400">Skills Created</div>
                  </div>
                </div>
              </div>

              {/* Objectives */}
              <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
                <h3 className="text-lg font-semibold mb-4">Objectives</h3>
                <div className="space-y-3">
                  {selectedCampaign.objectives?.map((objective) => (
                    <div key={objective.id} className="flex items-start gap-3 p-3 border border-slate-800 rounded">
                      <input
                        type="checkbox"
                        checked={objective.status === 'completed'}
                        readOnly
                        className="mt-1"
                      />
                      <div className="flex-1">
                        <p className={`${getObjectiveStatusColor(objective.status)}`}>
                          {objective.description}
                        </p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                          <span>Status: {objective.status}</span>
                          <span>Progress: {Math.round((objective.progress || 0) * 100)}%</span>
                          {objective.assigned_skills?.length > 0 && (
                            <span>Skills: {objective.assigned_skills.join(', ')}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  {(!selectedCampaign.objectives || selectedCampaign.objectives.length === 0) && (
                    <div className="text-slate-500 text-center py-4">No objectives yet.</div>
                  )}
                </div>
              </div>

              {/* Skills Generated */}
              <div className="border border-slate-700 rounded-lg p-4 bg-slate-900/40">
                <h3 className="text-lg font-semibold mb-4">Skills Generated</h3>
                <div className="grid grid-cols-2 gap-2">
                  {selectedCampaign.skills_generated?.map((skill) => (
                    <div key={skill} className="p-2 border border-slate-800 rounded bg-slate-950/60">
                      <span className="text-sm font-mono text-emerald-400">{skill}</span>
                    </div>
                  ))}
                  {(!selectedCampaign.skills_generated || selectedCampaign.skills_generated.length === 0) && (
                    <div className="col-span-2 text-slate-500 text-center py-4">No skills generated yet.</div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="border border-slate-700 rounded-lg p-8 bg-slate-900/40 text-center">
              <h3 className="text-lg font-medium text-slate-400 mb-2">Select a Campaign</h3>
              <p className="text-slate-500">Choose a campaign from the list to view its details, objectives, and generated skills.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
