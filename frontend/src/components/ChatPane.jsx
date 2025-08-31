import React from 'react'
import { api } from '../api'

export default function ChatPane(){
  const [msg,setMsg]=React.useState('')
  const [reply,setReply]=React.useState('')
  const [busy,setBusy]=React.useState(false)
  const [campaigns, setCampaigns] = React.useState([])
  const [selectedCampaign, setSelectedCampaign] = React.useState('')
  const [lastExecution, setLastExecution] = React.useState(null)
  const [collaborationSession, setCollaborationSession] = React.useState(null)
  
  React.useEffect(() => {
    loadCampaigns()
  }, [])
  
  const loadCampaigns = async () => {
    try {
      const { data } = await api.get('/campaigns')
      setCampaigns(data || [])
    } catch (error) {
      console.error('Failed to load campaigns:', error)
    }
  }
  
  const send=async()=>{ 
    if(!msg.trim()) return
    setBusy(true)
    setLastExecution(null)
    setCollaborationSession(null)
    
    try{ 
      const payload = { message: msg }
      if (selectedCampaign) {
        payload.campaign_id = selectedCampaign
      }
      
      const {data}=await api.post('/chat', payload)
      setReply(data.reply||'')
      
      if (data.executed) {
        setLastExecution(data.executed)
      }
      
      if (data.collaboration_session) {
        setCollaborationSession(data.collaboration_session)
      }
      
      if (data.campaign_updated) {
        loadCampaigns() // Refresh campaigns if one was updated
      }
      
      setMsg('') 
    }catch(e){ 
      alert('Chat failed: '+(e?.response?.data?.detail||e.message)) 
    } finally{ 
      setBusy(false) 
    } 
  }
  
  return (
    <div className="h-full flex flex-col">
      <div className="px-2 py-1 border-b border-slate-800 font-semibold text-sm">
        Chat with Dexter & Team
      </div>
      
      {/* Campaign Selection */}
      <div className="p-2 border-b border-slate-800 bg-slate-900/40">
        <select 
          value={selectedCampaign} 
          onChange={e => setSelectedCampaign(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs"
        >
          <option value="">No campaign (one-off request)</option>
          {campaigns.filter(c => c.status === 'active').map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>
      
      {/* Chat Display */}
      <div className="flex-1 overflow-auto p-2 text-sm space-y-2">
        {reply && (
          <div className="bg-slate-900 border border-slate-800 rounded p-2 text-slate-200 whitespace-pre-wrap">
            <div className="text-xs text-slate-400 mb-1">Dexter:</div>
            {reply}
          </div>
        )}
        
        {/* Execution Results */}
        {lastExecution && (
          <div className="bg-slate-900 border border-slate-800 rounded p-2">
            <div className="text-xs text-slate-400 mb-1">Skill Execution:</div>
            <div className={`text-xs ${lastExecution.ok ? 'text-green-400' : 'text-red-400'}`}>
              {lastExecution.ok ? '✓ Success' : '✗ Failed'}
            </div>
            {lastExecution.skill_name && (
              <div className="text-xs text-slate-300 mt-1">
                Skill: {lastExecution.skill_name}
              </div>
            )}
            {lastExecution.promoted && (
              <div className="text-xs text-emerald-400 mt-1">
                ✓ Promoted to skill library
              </div>
            )}
          </div>
        )}
        
        {/* Collaboration Status */}
        {collaborationSession && (
          <div className="bg-slate-900 border border-slate-800 rounded p-2">
            <div className="text-xs text-slate-400 mb-1">Team Collaboration:</div>
            <div className="text-xs text-blue-400">
              Session: {collaborationSession.slice(0, 8)}...
            </div>
            <div className="text-xs text-slate-300 mt-1">
              LLMs are working together in the background
            </div>
          </div>
        )}
      </div>
      
      {/* Input */}
      <div className="p-2 border-t border-slate-800 flex gap-2">
        <input 
          className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm" 
          placeholder={selectedCampaign ? "Add to campaign..." : "Ask Dexter anything..."} 
          value={msg} 
          onChange={e=>setMsg(e.target.value)} 
          onKeyDown={e=>e.key==='Enter'&&send()} 
          disabled={busy}
        />
        <button 
          onClick={send} 
          disabled={busy || !msg.trim()} 
          className="px-3 py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm"
        >
          {busy ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
