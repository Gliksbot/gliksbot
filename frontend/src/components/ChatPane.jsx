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
  const [skillsResults, setSkillsResults] = React.useState(null)
  const [isListening, setIsListening] = React.useState(false)
  const [speechSettings, setSpeechSettings] = React.useState({
    enabled: true,
    listenDuration: 5000, // 5 seconds default
    continuous: false
  })
  const [isMuted, setIsMuted] = React.useState(false)
  const recognitionRef = React.useRef(null)
  const synthRef = React.useRef(window.speechSynthesis)
  
  React.useEffect(() => {
    loadCampaigns()
    initializeSpeechRecognition()
  }, [])
  
  const initializeSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      
      recognitionRef.current.continuous = speechSettings.continuous
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'en-US'
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript
          }
        }
        
        if (finalTranscript) {
          setMsg(prev => prev + ' ' + finalTranscript.trim())
        }
      }
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
      }
      
      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }
  }
  
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
    setSkillsResults(null)
    
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
      
      if (data.skills_results) {
        setSkillsResults(data.skills_results)
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

  React.useEffect(() => {
    if (!isMuted && reply) {
      const utter = new SpeechSynthesisUtterance(reply)
      synthRef.current.cancel()
      synthRef.current.speak(utter)
    }
  }, [reply, isMuted])
  
  const startListening = () => {
    if (!speechSettings.enabled || !recognitionRef.current) return
    
    setIsListening(true)
    recognitionRef.current.start()
    
    // Auto-stop after configured duration
    setTimeout(() => {
      if (recognitionRef.current && isListening) {
        recognitionRef.current.stop()
      }
    }, speechSettings.listenDuration)
  }
  
  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
    }
    setIsListening(false)
  }
  
  const toggleMute = () => {
    setIsMuted(m => {
      const next = !m
      if (next) {
        synthRef.current.cancel()
      }
      return next
    })
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
        
        {/* Skills Results */}
        {skillsResults && skillsResults.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded p-2">
            <div className="text-xs text-slate-400 mb-1">Skills Executed:</div>
            <div className="space-y-1">
              {skillsResults.map((result, index) => (
                <div key={index} className="text-xs">
                  <div className={`flex items-center gap-2 ${result.success ? 'text-green-400' : 'text-red-400'}`}>
                    <span>{result.success ? '✓' : '✗'}</span>
                    <span className="font-medium">{result.skill_name}</span>
                  </div>
                  {result.result && (
                    <div className="text-slate-300 ml-4 mt-1">{result.result}</div>
                  )}
                  {result.error && (
                    <div className="text-red-300 ml-4 mt-1">{result.error}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Speech Settings Panel */}
      <div className="p-2 border-t border-slate-800 bg-slate-900/20">
        <div className="flex items-center gap-4 text-xs">
          <label className="flex items-center gap-1">
            <input 
              type="checkbox" 
              checked={speechSettings.enabled}
              onChange={(e) => setSpeechSettings(prev => ({...prev, enabled: e.target.checked}))}
              className="w-3 h-3"
            />
            <span className="text-slate-300">Speech Input</span>
          </label>
          
          <label className="flex items-center gap-1">
            <span className="text-slate-400">Duration:</span>
            <select 
              value={speechSettings.listenDuration}
              onChange={(e) => setSpeechSettings(prev => ({...prev, listenDuration: parseInt(e.target.value)}))}
              className="bg-slate-800 border border-slate-700 rounded px-1 py-0 text-xs"
              disabled={!speechSettings.enabled}
            >
              <option value={3000}>3s</option>
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
              <option value={15000}>15s</option>
              <option value={30000}>30s</option>
            </select>
          </label>
          
          <button 
            onClick={toggleMute}
            className={`px-2 py-1 rounded text-xs ${
              isMuted 
                ? 'bg-red-600 hover:bg-red-500 text-white' 
                : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
            }`}
          >
            {isMuted ? '🔇 Muted' : '🔊 Audio'}
          </button>
        </div>
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
        
        {/* Microphone Button */}
        {speechSettings.enabled && (
          <button 
            onClick={isListening ? stopListening : startListening}
            disabled={busy}
            className={`px-3 py-2 rounded text-sm ${
              isListening 
                ? 'bg-red-600 hover:bg-red-500 text-white' 
                : 'bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white'
            }`}
          >
            {isListening ? '🎤 Stop' : '🎤'}
          </button>
        )}
        
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
