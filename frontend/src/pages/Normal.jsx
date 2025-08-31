import React, { useState, useEffect, useRef } from 'react'
import { api } from '../api'

export default function Normal() {
  const [request, setRequest] = useState('')
  const [loading, setLoading] = useState(false)
  const [chatHistory, setChatHistory] = useState([])
  const [isListening, setIsListening] = useState(false)
  const [userMuted, setUserMuted] = useState(false)
  const [dexterMuted, setDexterMuted] = useState(false)
  const [llmSlots, setLlmSlots] = useState({})
  const [collaborationActive, setCollaborationActive] = useState(false)
  
  const recognitionRef = useRef(null)
  const synthRef = useRef(null)
  const chatContainerRef = useRef(null)

  useEffect(() => {
    loadChatHistory()
    loadLlmSlots()
    initializeSpeech()
    
    // Set up collaboration polling
    const interval = setInterval(loadLlmSlots, 2000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Auto-scroll chat to bottom
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatHistory])

  const initializeSpeech = () => {
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = false
      
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        setRequest(transcript)
      }
      
      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }
    
    // Initialize speech synthesis
    synthRef.current = window.speechSynthesis
  }

  const loadChatHistory = async () => {
    try {
      const { data } = await api.get('/history')
      setChatHistory(data?.interactions || [])
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }

  const loadLlmSlots = async () => {
    try {
      const { data } = await api.get('/collaboration/status')
      setLlmSlots(data?.slots || {})
      setCollaborationActive(data?.active || false)
    } catch (error) {
      console.error('Failed to load LLM slots:', error)
    }
  }

  const toggleListening = () => {
    if (!recognitionRef.current || userMuted) return
    
    if (isListening) {
      recognitionRef.current.stop()
    } else {
      recognitionRef.current.start()
      setIsListening(true)
    }
  }

  const speakResponse = (text) => {
    if (!synthRef.current || dexterMuted) return
    
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 0.9
    utterance.pitch = 1
    synthRef.current.speak(utterance)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!request.trim() || loading) return

    setLoading(true)
    const userMessage = request.trim()
    setRequest('')

    // Add user message to chat immediately
    const newMessage = {
      id: Date.now(),
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    }
    setChatHistory(prev => [...prev, newMessage])

    try {
      const { data } = await api.post('/chat', {
        message: userMessage,
        mode: 'normal'
      })
      
      // Add Dexter's response to chat
      const responseMessage = {
        id: Date.now() + 1,
        type: 'dexter',
        content: data.response || data.reply || 'No response received',
        timestamp: new Date().toISOString()
      }
      setChatHistory(prev => [...prev, responseMessage])
      
      // Speak the response
      speakResponse(responseMessage.content)
      
      // Refresh LLM slots to show any collaboration
      loadLlmSlots()
      
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Error: ' + (error?.response?.data?.detail || error.message),
        timestamp: new Date().toISOString()
      }
      setChatHistory(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const renderLlmSlot = (slotId, slotData) => {
    if (!slotData) {
      return (
        <div key={slotId} className="border border-slate-700 rounded-lg p-3 bg-slate-900/40 min-h-[120px]">
          <div className="text-xs text-slate-500 mb-2">Slot {slotId}</div>
          <div className="text-slate-600 text-center py-8 text-sm">Not configured</div>
        </div>
      )
    }

    if (slotData.error) {
      return (
        <div key={slotId} className="border border-red-700 rounded-lg p-3 bg-red-900/20 min-h-[120px]">
          <div className="text-xs text-red-400 mb-2">Slot {slotId} - ERROR</div>
          <div className="text-red-300 text-sm">{slotData.error}</div>
        </div>
      )
    }

    return (
      <div key={slotId} className="border border-slate-700 rounded-lg p-3 bg-slate-900/40 min-h-[120px]">
        <div className="text-xs text-slate-400 mb-2 flex justify-between">
          <span>Slot {slotId} - {slotData.name || 'Unknown'}</span>
          {slotData.active && <span className="text-green-400">●</span>}
        </div>
        <div className="text-slate-300 text-sm">
          {slotData.currentTask && (
            <div className="mb-2 p-2 bg-slate-800 rounded text-xs">
              <strong>Current:</strong> {slotData.currentTask}
            </div>
          )}
          {slotData.output && (
            <div className="text-xs text-slate-400 max-h-16 overflow-y-auto">
              {slotData.output.split('\n').slice(-3).join('\n')}
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 max-w-7xl mx-auto h-screen flex flex-col">
      <h1 className="text-2xl font-bold mb-6">Chat with Dexter</h1>
      
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Chat History */}
          <div 
            ref={chatContainerRef}
            className="flex-1 border border-slate-700 rounded-lg p-4 bg-slate-900/40 overflow-y-auto mb-4"
          >
            <div className="space-y-3">
              {chatHistory.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-3 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-emerald-600 text-white' 
                      : message.type === 'error'
                      ? 'bg-red-600 text-white'
                      : 'bg-slate-700 text-slate-200'
                  }`}>
                    <div className="text-xs opacity-70 mb-1">
                      {message.type === 'user' ? 'You' : message.type === 'error' ? 'Error' : 'Dexter'} - {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-700 text-slate-200 p-3 rounded-lg">
                    <div className="text-xs opacity-70 mb-1">Dexter is thinking...</div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chat Input */}
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="flex-1 relative">
              <input
                type="text"
                value={request}
                onChange={(e) => setRequest(e.target.value)}
                placeholder="Type your message to Dexter..."
                className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 pr-12"
                disabled={loading}
              />
              <button
                type="button"
                onClick={toggleListening}
                disabled={userMuted || !recognitionRef.current}
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 p-2 rounded ${
                  isListening 
                    ? 'bg-red-600 text-white' 
                    : 'bg-slate-600 hover:bg-slate-500 text-slate-300'
                } disabled:opacity-50`}
              >
                🎤
              </button>
            </div>
            
            <button
              type="button"
              onClick={() => setUserMuted(!userMuted)}
              className={`px-3 py-2 rounded ${
                userMuted 
                  ? 'bg-red-600 text-white' 
                  : 'bg-slate-600 hover:bg-slate-500 text-slate-300'
              }`}
            >
              {userMuted ? '🔇' : '🔊'}
            </button>
            
            <button
              type="button"
              onClick={() => setDexterMuted(!dexterMuted)}
              className={`px-3 py-2 rounded ${
                dexterMuted 
                  ? 'bg-red-600 text-white' 
                  : 'bg-slate-600 hover:bg-slate-500 text-slate-300'
              }`}
              title="Mute Dexter's voice"
            >
              {dexterMuted ? '🔇 D' : '🔊 D'}
            </button>

            <button
              type="submit"
              disabled={loading || !request.trim()}
              className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium"
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>

        {/* LLM Collaboration Pane */}
        <div className="w-96 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">LLM Collaboration</h2>
            <div className={`w-3 h-3 rounded-full ${collaborationActive ? 'bg-green-400' : 'bg-slate-600'}`}></div>
          </div>
          
          <div className="flex-1 grid grid-cols-1 gap-3 auto-rows-min">
            {/* Dexter's slot (always show status) */}
            <div className="border border-emerald-700 rounded-lg p-3 bg-emerald-900/20">
              <div className="text-xs text-emerald-400 mb-2">Dexter (Main)</div>
              <div className="text-emerald-300 text-sm">
                {loading ? 'Processing your request...' : 'Ready'}
              </div>
            </div>
            
            {/* Other LLM slots */}
            {[1, 2, 3, 4, 5].map(slotNum => 
              renderLlmSlot(slotNum, llmSlots[`slot_${slotNum}`])
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
