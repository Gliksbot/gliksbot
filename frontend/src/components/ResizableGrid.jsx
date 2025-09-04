import React, { useState, useEffect, useRef } from 'react'
import { api } from '../api'
import ChatPane from './ChatPane'

// TTS Manager for speech synthesis
class TTSManager {
  constructor() {
    this.synth = window.speechSynthesis
    this.voices = []
    this.settings = {
      enabled: true,
      rate: 1.0,
      pitch: 1.0,
      volume: 0.8,
      voice: null
    }
    this.loadVoices()
  }

  loadVoices() {
    this.voices = this.synth.getVoices()
    if (this.voices.length === 0) {
      // Fallback for browsers that load voices asynchronously
      this.synth.onvoiceschanged = () => {
        this.voices = this.synth.getVoices()
      }
    }
  }

  speak(text, customSettings = {}) {
    if (!this.settings.enabled || !text || !this.synth) return

    // Cancel any ongoing speech
    this.synth.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = customSettings.rate || this.settings.rate
    utterance.pitch = customSettings.pitch || this.settings.pitch
    utterance.volume = customSettings.volume || this.settings.volume
    
    if (customSettings.voice || this.settings.voice) {
      utterance.voice = customSettings.voice || this.settings.voice
    }

    this.synth.speak(utterance)
  }

  stop() {
    this.synth.cancel()
  }

  getVoices() {
    return this.voices
  }

  updateSettings(newSettings) {
    this.settings = { ...this.settings, ...newSettings }
  }
}

// Global TTS instance
const tts = new TTSManager()

// Collaboration Pane Component
function CollabPane({ slotName }) {
  const [preview, setPreview] = useState('')
  const [loading, setLoading] = useState(false)
  const [userInput, setUserInput] = useState('')
  const [lastUpdate, setLastUpdate] = useState(Date.now())
  const [error, setError] = useState('')
  
  const loadCollabData = async () => {
    try {
      setError('')
      const response = await api.get(`/collaboration/head?slot=${slotName}&n=1`)
      if (response.data?.items?.length > 0) {
        const latestItem = response.data.items[0]
        let displayText = latestItem.text || JSON.stringify(latestItem)
        setPreview(displayText)
        setLastUpdate(Date.now())
      } else {
        setPreview('No recent collaboration activity')
      }
    } catch (err) {
      setError('Error loading collaboration data: ' + err.message)
      setPreview('Error loading data')
    }
  }
  
  const sendUserInput = async () => {
    if (!userInput.trim()) return
    
    setLoading(true)
    try {
      const response = await api.post(`/collaboration/input/${slotName}`, {
        message: userInput,
      })
      
      if (response.data.success) {
        setUserInput('')
        // Refresh collaboration data to show the response
        setTimeout(loadCollabData, 1000)
      } else {
        setError('Error: ' + (response.data.error || 'Failed to send message'))
      }
    } catch (error) {
      setError('Error sending message: ' + error.message)
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    loadCollabData()
    
    // Auto-refresh every 2 minutes (reduced from 5 seconds to reduce UI churn)
    const interval = setInterval(loadCollabData, 120000) // Changed from 5000ms to 120000ms
    return () => clearInterval(interval)
  }, [slotName])
  
  return (
    <div className="h-full flex flex-col p-3 space-y-3">
      {/* Header with refresh */}
      <div className="flex items-center justify-between">
        <h5 className="text-sm font-medium text-white">Collaboration Activity</h5>
        <button 
          onClick={loadCollabData}
          className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-1 rounded text-white"
          title="Refresh collaboration data"
        >
          🔄 Refresh
        </button>
      </div>
      
      {/* User Input Section */}
      <div className="space-y-2">
        <label className="text-xs text-slate-300">Send message to {slotName}:</label>
        <div className="flex space-x-2">
          <input
            type="text"
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendUserInput()}
            placeholder="Type your message..."
            className="flex-1 text-xs px-2 py-1 bg-slate-800 border border-slate-600 rounded text-white placeholder-slate-400"
            disabled={loading}
          />
          <button
            onClick={sendUserInput}
            disabled={loading || !userInput.trim()}
            className="text-xs bg-green-600 hover:bg-green-500 disabled:bg-gray-600 px-3 py-1 rounded text-white"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
      
      {/* Error Display */}
      {error && (
        <div className="text-xs bg-red-900 border border-red-600 rounded p-2 text-red-200">
          {error}
        </div>
      )}
      
      {/* Collaboration Content */}
      <div className="flex-1 bg-slate-800 border border-slate-600 rounded p-2 overflow-auto">
        <div className="text-xs font-mono text-slate-300 whitespace-pre-wrap">
          {preview || 'Loading collaboration data...'}
        </div>
      </div>
      
      {/* Footer with update time */}
      <div className="text-xs text-slate-500 text-center">
        Last updated: {new Date(lastUpdate).toLocaleTimeString()}
      </div>
    </div>
  )
}

// Individual LLM Chat & Config Interface
function LLMInterface({ slotName, events, isActive, config, onConfigUpdate }) {
  const [activeTab, setActiveTab] = useState('chat') // 'chat', 'config', 'monitor', 'tts'
  const [isMinimized, setIsMinimized] = useState(false)
  
  // Load chat history from localStorage
  const loadChatHistory = () => {
    try {
      const savedHistory = localStorage.getItem(`dexter_chat_${slotName}`)
      return savedHistory ? JSON.parse(savedHistory) : []
    } catch (e) {
      console.warn(`Failed to load chat history for ${slotName}:`, e)
      return []
    }
  }
  
  const [chatHistory, setChatHistory] = useState(loadChatHistory)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [ttsSettings, setTtsSettings] = useState({
    enabled: true,
    rate: 1.0,
    pitch: 1.0,
    volume: 0.8,
    voice: null
  })
  const [modelConfig, setModelConfig] = useState(config || {
    enabled: false,
    provider: 'ollama',
    model: '',
    endpoint: 'http://localhost:11434',
    api_key_env: '',
    temperature: 0.7,
    max_tokens: 2048,
    local_model: false,
    identity: '',
    role: ''
  })

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem(`dexter_chat_${slotName}`, JSON.stringify(chatHistory))
    } catch (e) {
      console.warn(`Failed to save chat history for ${slotName}:`, e)
    }
  }, [chatHistory, slotName])

  // Update local config when prop changes and sync to backend
  useEffect(() => {
    if (config) {
      const newConfig = {
        enabled: config.enabled ?? false,
        provider: config.provider || 'ollama',
        model: config.model || '',
        endpoint: config.endpoint || 'http://localhost:11434',
        api_key_env: config.api_key_env || '',
        temperature: config.params?.temperature ?? config.temperature ?? 0.7,
        max_tokens: config.params?.max_tokens ?? config.max_tokens ?? 2048,
        local_model: config.local_model ?? false,
        identity: config.identity || '',
        role: config.role || '',
        prompt: config.prompt || ''
      }
      
      // Only update if the config actually changed to prevent infinite loops
      if (JSON.stringify(newConfig) !== JSON.stringify(modelConfig)) {
        console.log(`${slotName} config updated from parent:`, newConfig)
        setModelConfig(newConfig)
      }
    }
  }, [config, slotName])

  // Reduced config sync polling - only poll every 60 seconds to reduce UI churn
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const { data } = await api.get('/config')
        const serverConfig = data?.config?.models?.[slotName]
        if (serverConfig && JSON.stringify(serverConfig) !== JSON.stringify(config)) {
          // Config changed on server, update parent state
          onConfigUpdate?.(slotName, serverConfig)
        }
      } catch (error) {
        // Silently handle polling errors
      }
    }, 60000) // Changed from 3000ms to 60000ms (1 minute)

    return () => clearInterval(interval)
  }, [slotName, config, onConfigUpdate])

  const bottomRef = useRef(null)
  const chatContainerRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatHistory])

  // Auto-scroll for events
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const slotEvents = events.filter(e => e.slot === slotName)

  const handleConfigChange = async (field, value) => {
    const newConfig = { ...modelConfig, [field]: value }
    console.log(`${slotName} ${field} changed to:`, value)
    
    // Update local state immediately for responsive UI
    setModelConfig(newConfig)
    
    // Notify parent immediately
    onConfigUpdate?.(slotName, newConfig)
  }

  const handleTtsSettingsChange = (field, value) => {
    const newTtsSettings = { ...ttsSettings, [field]: value }
    setTtsSettings(newTtsSettings)
    tts.updateSettings(newTtsSettings)
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!message.trim() || loading) return

    setLoading(true)
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString()
    }
    
    setChatHistory(prev => [...prev, userMessage])
    setMessage('')

    try {
      const { data } = await api.post('/llm/chat', {
        message: userMessage.content,
        model: slotName,
        config: modelConfig
      })
      
      const responseText = data.response || data.reply || 'No response received'
      const llmResponse = {
        id: Date.now() + 1,
        type: 'llm',
        content: responseText,
        timestamp: new Date().toISOString()
      }
      
      setChatHistory(prev => [...prev, llmResponse])
      
      // TTS for LLM response
      if (ttsSettings.enabled && responseText) {
        // Use a slight delay to let the UI update first
        setTimeout(() => {
          tts.speak(responseText, ttsSettings)
        }, 100)
      }
      
    } catch (error) {
      const errorResponse = {
        id: Date.now() + 1,
        type: 'error',
        content: `Error: ${error?.response?.data?.error || error?.response?.data?.detail || error.message}`,
        timestamp: new Date().toISOString()
      }
      setChatHistory(prev => [...prev, errorResponse])
    } finally {
      setLoading(false)
    }
  }

  const saveConfig = async () => {
    try {
      await api.post('/config/models', {
        [slotName]: modelConfig
      })
      // Show success feedback
    } catch (error) {
      console.error('Failed to save config:', error)
    }
  }

  if (isMinimized) {
    return (
      <div className="h-12 bg-slate-900 border border-slate-600 rounded-lg flex items-center justify-between px-3">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-medium text-white capitalize">{slotName}</h4>
          <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-400' : 'bg-slate-500'}`}></div>
          {modelConfig.enabled && <span className="text-xs text-green-400">●</span>}
        </div>
        <button 
          onClick={() => setIsMinimized(false)}
          className="text-slate-400 hover:text-white"
        >
          ⬆️
        </button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-slate-900 border border-slate-600 rounded-lg overflow-hidden">
      {/* Header with tabs and controls */}
      <div className={`p-2 border-b border-slate-600 ${isActive ? 'bg-green-800' : 'bg-slate-800'}`}>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-white capitalize">{slotName}</h4>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-green-400' : 'bg-slate-500'}`}></div>
            <button 
              onClick={() => setIsMinimized(true)}
              className="text-slate-400 hover:text-white text-xs"
            >
              ⬇️
            </button>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="flex gap-1">
          {['chat', 'collab', 'config', 'monitor', 'tts'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-2 py-1 text-xs rounded ${
                activeTab === tab 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
              }`}
            >
              {tab === 'chat' ? '💬' : 
               tab === 'collab' ? '🤝' :
               tab === 'config' ? '⚙️' : 
               tab === 'monitor' ? '📊' : 
               '🔊'} {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {activeTab === 'chat' && (
          <div className="flex-1 flex flex-col min-h-0">
            {/* Chat History with proper scrolling container */}
            <div 
              ref={chatContainerRef}
              className="flex-1 overflow-y-auto p-2 space-y-2 min-h-0"
              style={{ maxHeight: 'calc(100% - 60px)' }}
            >
              {chatHistory.length === 0 ? (
                <div className="text-center text-slate-500 text-sm mt-8">
                  <div className="text-2xl mb-2">🤖</div>
                  <div>Start chatting with {slotName}</div>
                  {ttsSettings.enabled && (
                    <div className="text-xs mt-2 text-green-400">🔊 TTS enabled</div>
                  )}
                </div>
              ) : (
                <>
                  {chatHistory.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] p-2 rounded text-xs relative group ${
                        msg.type === 'user' 
                          ? 'bg-blue-600 text-white' 
                          : msg.type === 'error'
                          ? 'bg-red-600 text-white'
                          : 'bg-slate-700 text-slate-100'
                      }`}>
                        <div className="opacity-70 mb-1 flex items-center justify-between">
                          <span>{msg.type === 'user' ? 'You' : msg.type === 'error' ? 'Error' : slotName}</span>
                          {msg.type === 'llm' && (
                            <button
                              onClick={() => tts.speak(msg.content, ttsSettings)}
                              className="opacity-0 group-hover:opacity-100 transition-opacity ml-2 hover:text-blue-300"
                              title="Speak this message"
                            >
                              🔊
                            </button>
                          )}
                        </div>
                        <div className="leading-relaxed whitespace-pre-wrap break-words">{msg.content}</div>
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-slate-700 text-slate-200 p-2 rounded text-xs">
                        <div className="flex space-x-1">
                          <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce"></div>
                          <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                          <div className="w-1 h-1 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Chat Input - Fixed at bottom */}
            <div className="flex-shrink-0 p-2 border-t border-slate-600 bg-slate-900">
              <form onSubmit={sendMessage} className="flex gap-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder={`Message ${slotName}...`}
                  className="flex-1 bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-400"
                  disabled={loading || !modelConfig.enabled}
                />
                <button
                  type="submit"
                  disabled={loading || !message.trim() || !modelConfig.enabled}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-2 py-1 rounded text-xs"
                >
                  Send
                </button>
                <button
                  type="button"
                  onClick={() => tts.stop()}
                  className="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs"
                  title="Stop speech"
                >
                  🔇
                </button>
              </form>
            </div>
          </div>
        )}

        {activeTab === 'collab' && (
          <CollabPane slotName={slotName} />
        )}

        {activeTab === 'config' && (
          <div className="h-full overflow-auto p-3 space-y-3">
            {/* Config Sync Status and Refresh */}
            <div className="flex items-center justify-between p-2 bg-slate-800 rounded border border-slate-600">
              <div className="flex items-center gap-2 text-xs">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-slate-300">Config synced with file</span>
              </div>
              <button
                onClick={async () => {
                  try {
                    const { data } = await api.get('/config')
                    const serverConfig = data?.config?.models?.[slotName]
                    if (serverConfig) {
                      onConfigUpdate?.(slotName, serverConfig)
                    }
                  } catch (error) {
                    console.error('Failed to refresh config:', error)
                  }
                }}
                className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded"
              >
                🔄 Refresh
              </button>
            </div>

            {/* Enable/Disable */}
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-white">Enabled</label>
              <input
                type="checkbox"
                checked={modelConfig.enabled}
                onChange={(e) => handleConfigChange('enabled', e.target.checked)}
                className="rounded"
              />
            </div>

            {/* Provider */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">Provider</label>
              <select
                value={modelConfig.provider}
                onChange={(e) => handleConfigChange('provider', e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white"
              >
                <option value="ollama">Ollama</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="vultr">Vultr</option>
                <option value="nvidia">NVIDIA</option>
                <option value="custom">Custom API</option>
              </select>
            </div>

            {/* Model Name */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">Model</label>
              <input
                type="text"
                value={modelConfig.model}
                onChange={(e) => handleConfigChange('model', e.target.value)}
                placeholder="e.g., llama3, gpt-4o, claude-3"
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-400"
              />
            </div>

            {/* Identity */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">Identity</label>
              <textarea
                value={modelConfig.identity || ''}
                onChange={(e) => handleConfigChange('identity', e.target.value)}
                placeholder="Who is this LLM? Define their personality and expertise..."
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-400 h-16 resize-none"
              />
            </div>

            {/* Role */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">Role</label>
              <input
                type="text"
                value={modelConfig.role || ''}
                onChange={(e) => handleConfigChange('role', e.target.value)}
                placeholder="e.g., Senior Software Engineer, Data Analyst"
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-400"
              />
            </div>

            {/* Prompt */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">System Prompt</label>
              <textarea
                value={modelConfig.prompt || ''}
                onChange={(e) => handleConfigChange('prompt', e.target.value)}
                placeholder="Additional instructions and context for this LLM..."
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-400 h-20 resize-none"
              />
            </div>

            {/* Endpoint URL */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">Endpoint URL</label>
              <input
                type="text"
                value={modelConfig.endpoint}
                onChange={(e) => handleConfigChange('endpoint', e.target.value)}
                placeholder="http://localhost:11434"
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-400"
              />
            </div>

            {/* API Key */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">API Key Environment Variable</label>
              <input
                type="text"
                value={modelConfig.api_key_env}
                onChange={(e) => handleConfigChange('api_key_env', e.target.value)}
                placeholder="OPENAI_API_KEY, ANTHROPIC_API_KEY, etc."
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-400"
              />
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">
                Temperature: {modelConfig.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={modelConfig.temperature}
                onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Max Tokens */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">Max Tokens</label>
              <input
                type="number"
                value={modelConfig.max_tokens}
                onChange={(e) => handleConfigChange('max_tokens', parseInt(e.target.value) || 2048)}
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white"
              />
            </div>

            {/* Local Model Toggle */}
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-white">Local Model</label>
              <input
                type="checkbox"
                checked={modelConfig.local_model}
                onChange={(e) => handleConfigChange('local_model', e.target.checked)}
                className="rounded"
              />
            </div>

            {/* Save Button */}
            <button
              onClick={saveConfig}
              className="w-full bg-green-600 hover:bg-green-700 text-white py-2 rounded text-xs font-medium"
            >
              Save Configuration
            </button>
          </div>
        )}

        {activeTab === 'tts' && (
          <div className="h-full overflow-auto p-3 space-y-3">
            {/* TTS Enable/Disable */}
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-white">Enable Text-to-Speech</label>
              <input
                type="checkbox"
                checked={ttsSettings.enabled}
                onChange={(e) => handleTtsSettingsChange('enabled', e.target.checked)}
                className="rounded"
              />
            </div>

            {/* Voice Selection */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">Voice</label>
              <select
                value={ttsSettings.voice?.name || ''}
                onChange={(e) => {
                  const voice = tts.getVoices().find(v => v.name === e.target.value)
                  handleTtsSettingsChange('voice', voice)
                }}
                className="w-full bg-slate-800 border border-slate-600 rounded px-2 py-1 text-xs text-white"
                disabled={!ttsSettings.enabled}
              >
                <option value="">Default Voice</option>
                {tts.getVoices().map((voice, i) => (
                  <option key={i} value={voice.name}>
                    {voice.name} ({voice.lang})
                  </option>
                ))}
              </select>
            </div>

            {/* Rate */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">
                Speech Rate: {ttsSettings.rate}x
              </label>
              <input
                type="range"
                min="0.1"
                max="3"
                step="0.1"
                value={ttsSettings.rate}
                onChange={(e) => handleTtsSettingsChange('rate', parseFloat(e.target.value))}
                className="w-full"
                disabled={!ttsSettings.enabled}
              />
            </div>

            {/* Pitch */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">
                Pitch: {ttsSettings.pitch}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={ttsSettings.pitch}
                onChange={(e) => handleTtsSettingsChange('pitch', parseFloat(e.target.value))}
                className="w-full"
                disabled={!ttsSettings.enabled}
              />
            </div>

            {/* Volume */}
            <div>
              <label className="block text-xs font-medium text-white mb-1">
                Volume: {Math.round(ttsSettings.volume * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={ttsSettings.volume}
                onChange={(e) => handleTtsSettingsChange('volume', parseFloat(e.target.value))}
                className="w-full"
                disabled={!ttsSettings.enabled}
              />
            </div>

            {/* Test Speech */}
            <div>
              <button
                onClick={() => tts.speak(`Hello, this is ${slotName} speaking. This is a test of the text-to-speech system.`, ttsSettings)}
                disabled={!ttsSettings.enabled}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white py-2 rounded text-xs font-medium"
              >
                🔊 Test Voice
              </button>
            </div>

            {/* Stop Speech */}
            <div>
              <button
                onClick={() => tts.stop()}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-2 rounded text-xs font-medium"
              >
                🔇 Stop Speech
              </button>
            </div>
          </div>
        )}

        {activeTab === 'monitor' && (
          <div className="h-full overflow-auto p-2 space-y-1">
            <div className="text-xs text-slate-400 mb-2">
              Activity: {slotEvents.length} events
            </div>
            {slotEvents.length === 0 ? (
              <div className="text-center text-slate-500 text-sm mt-4">
                <div className="text-2xl mb-2">💤</div>
                <div>No activity yet</div>
              </div>
            ) : (
              slotEvents.map((event, i) => (
                <div key={i} className="text-xs bg-slate-800/50 rounded p-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-slate-400">
                      {new Date(event.ts * 1000).toLocaleTimeString()}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                      event.event.includes('error') ? 'bg-red-800 text-red-200' :
                      event.event.includes('completed') ? 'bg-green-800 text-green-200' :
                      event.event.includes('started') ? 'bg-blue-800 text-blue-200' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      {event.event}
                    </span>
                  </div>
                  {event.text && (
                    <div className="text-slate-300 text-xs leading-relaxed">
                      {event.text}
                    </div>
                  )}
                </div>
              ))
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  )
}

// Resizable pane component
function ResizablePane({ children, className = "", style = {} }) {
  const [isResizing, setIsResizing] = useState(false)
  const [dimensions, setDimensions] = useState({ width: '300px', height: '400px' })
  const paneRef = useRef(null)
  
  const startResize = (e) => {
    setIsResizing(true)
    e.preventDefault()
  }
  
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing || !paneRef.current) return
      
      const rect = paneRef.current.getBoundingClientRect()
      const newWidth = e.clientX - rect.left + 'px'
      const newHeight = e.clientY - rect.top + 'px'
      
      setDimensions({ width: newWidth, height: newHeight })
    }
    
    const handleMouseUp = () => {
      setIsResizing(false)
    }
    
    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing])
  
  return (
    <div 
      ref={paneRef}
      className={`relative ${className}`}
      style={{ ...dimensions, ...style, minWidth: '200px', minHeight: '150px' }}
    >
      {children}
      
      {/* Resize handle */}
      <div 
        className="absolute bottom-0 right-0 w-4 h-4 bg-slate-600 cursor-se-resize hover:bg-slate-500 transition-colors"
        onMouseDown={startResize}
        style={{ clipPath: 'polygon(100% 0%, 0% 100%, 100% 100%)' }}
      />
    </div>
  )
}

// Main LLM management grid
export default function ResizableGrid() {
  // Load events from localStorage on startup
  const loadEventsFromStorage = () => {
    try {
      const savedEvents = localStorage.getItem('dexter_events')
      return savedEvents ? JSON.parse(savedEvents) : []
    } catch (e) {
      console.warn('Failed to load events from localStorage:', e)
      return []
    }
  }
  
  const [events, setEvents] = useState(loadEventsFromStorage)
  const [paused, setPaused] = useState(false)
  const [activeSlots, setActiveSlots] = useState(new Set())
  const [modelConfigs, setModelConfigs] = useState({})
  const [loading, setLoading] = useState(true)
  const [configVersion, setConfigVersion] = useState(0) // Force re-renders on config changes
  
  // Save events to localStorage whenever they change (prevent data loss on reload)
  useEffect(() => {
    try {
      // Keep only the last 1000 events to prevent localStorage bloat
      const eventsToSave = events.slice(-1000)
      localStorage.setItem('dexter_events', JSON.stringify(eventsToSave))
    } catch (e) {
      console.warn('Failed to save events to localStorage:', e)
    }
  }, [events])
  
  // Known LLM slots - using actual model names from config
  const slots = ['dexter', 'analyst', 'engineer', 'researcher', 'creative', 'specialist1', 'specialist2', 'rye']
  
  // Load model configurations from backend
  const loadConfigs = async () => {
    setLoading(true)
    try {
      console.log('🔄 Loading configs from backend...')
      
      // Try public endpoint first, then auth endpoint as fallback
      let response
      try {
        response = await api.get('/config/public')
        console.log('✅ Using public config endpoint')
      } catch (publicError) {
        console.log('⚠️ Public endpoint failed, trying auth endpoint')
        response = await api.get('/config')
        console.log('✅ Using authenticated config endpoint')
      }
      
      const newConfigs = response.data?.config?.models || {}
      console.log('📋 Loaded configs for slots:', Object.keys(newConfigs))
      
      setModelConfigs(newConfigs)
      setConfigVersion(prev => prev + 1) // Force UI refresh
      
      console.log('✅ Config sync complete')
    } catch (error) {
      console.error('❌ Failed to load model configs:', error)
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    loadConfigs()
  }, [])

  // Poll for config changes every 30 seconds to catch external file changes (reduced from 2 seconds)
  useEffect(() => {
    const interval = setInterval(() => {
      loadConfigs()
    }, 30000) // Changed from 2000ms to 30000ms
    
    return () => clearInterval(interval)
  }, [])

  // Handle events stream with reconnection logic
  useEffect(() => {
    let es = null
    let reconnectAttempts = 0
    const maxReconnectAttempts = 5
    const baseReconnectDelay = 1000 // 1 second
    
    const connectSSE = () => {
      console.log('🔌 Connecting to SSE...')
      es = new EventSource('/events')
      
      es.onopen = () => {
        console.log('✅ SSE connected')
        reconnectAttempts = 0 // Reset on successful connection
      }
      
      es.onmessage = (m) => {
        if (paused) return
        try {
          const event = JSON.parse(m.data)
          setEvents(prev => [...prev.slice(-999), event])
          
          // Track active slots
          if (event.slot) {
            setActiveSlots(prev => new Set([...prev, event.slot]))
          }
        } catch (e) {
          console.error('Failed to parse event:', e)
        }
      }
      
      es.onerror = (e) => {
        console.error('❌ SSE error:', e)
        es.close()
        
        // Implement exponential backoff for reconnection
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts)
          console.log(`🔄 Reconnecting SSE in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`)
          
          setTimeout(() => {
            reconnectAttempts++
            connectSSE()
          }, delay)
        } else {
          console.error('🚫 Max SSE reconnection attempts reached. Manual refresh may be needed.')
        }
      }
    }
    
    connectSSE()
    
    return () => {
      if (es) {
        es.close()
      }
    }
  }, [paused])

  // Handle configuration updates with immediate backend sync
  const handleConfigUpdate = async (slotName, config) => {
    console.log(`Updating config for ${slotName}:`, config)
    
    // Update local state immediately for responsive UI
    setModelConfigs(prev => ({
      ...prev,
      [slotName]: config
    }))
    
    // Sync to backend immediately (this updates config.json)
    try {
      await api.post(`/system/models/${slotName}/config`, config)
      console.log(`Successfully saved ${slotName} config to backend`)
      
      // Force reload after a short delay to ensure consistency
      setTimeout(() => {
        loadConfigs()
      }, 500)
      
    } catch (error) {
      console.error(`Failed to save ${slotName} config:`, error)
      // Revert local changes on error
      loadConfigs()
    }
  }

  // Clear all chats
  const clearAllChats = () => {
    // Clear localStorage for all chat histories and events
    try {
      const keysToRemove = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && (key.startsWith('dexter_chat_') || key === 'dexter_events')) {
          keysToRemove.push(key)
        }
      }
      
      keysToRemove.forEach(key => localStorage.removeItem(key))
      console.log('🗑️ Cleared chat histories and events from localStorage')
      
      // Reset events state
      setEvents([])
      
      // Note: Individual chat histories will be cleared on next render due to localStorage clearing
      
    } catch (e) {
      console.warn('Failed to clear chat data:', e)
    }
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="text-2xl mb-2">⚙️</div>
          <div className="text-white">Loading LLM configurations...</div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="h-full p-4 bg-slate-950 overflow-auto">
      {/* Controls */}
      <div className="mb-4 flex items-center gap-4 p-3 bg-slate-800 rounded-lg">
        <h2 className="text-lg font-semibold text-white">LLM Team Interface</h2>
        <button 
          onClick={() => setPaused(p => !p)}
          className={`px-3 py-1 rounded text-sm font-medium ${
            paused ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
          } text-white transition-colors`}
        >
          {paused ? '▶️ Resume Events' : '⏸️ Pause Events'}
        </button>
        <button 
          onClick={clearAllChats}
          className="px-3 py-1 rounded text-sm font-medium bg-gray-600 hover:bg-gray-700 text-white transition-colors"
        >
          🗑️ Clear All Chats
        </button>
        <button 
          onClick={async () => {
            try {
              const { data } = await api.get('/config/public')
              setModelConfigs(data?.config?.models || {})
              setConfigVersion(prev => prev + 1)
            } catch (error) {
              console.error('Failed to reload configs:', error)
              // Fallback: try auth endpoint
              try {
                const { data } = await api.get('/config')
                setModelConfigs(data?.config?.models || {})
                setConfigVersion(prev => prev + 1)
              } catch (authError) {
                console.error('Both config endpoints failed:', authError)
              }
            }
          }}
          className="px-3 py-1 rounded text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors"
        >
          🔄 Reload All Configs
        </button>
        <div className="text-sm text-slate-400">
          Events: {events.length} | Active: {activeSlots.size} | 
          Enabled: {Object.values(modelConfigs).filter(c => c?.enabled).length}/{slots.length}
        </div>
      </div>
      
      {/* Unified Chat with Dexter & Team */}
      <div className="mb-6">
        <ResizablePane className="w-full min-h-[400px]">
          <ChatPane />
        </ResizablePane>
      </div>
      
      {/* Individual LLM Interfaces Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {slots.map(slot => (
          <ResizablePane key={slot} className="min-h-[400px]">
            <LLMInterface 
              slotName={slot}
              events={events}
              isActive={activeSlots.has(slot)}
              config={modelConfigs[slot]}
              onConfigUpdate={handleConfigUpdate}
            />
          </ResizablePane>
        ))}
      </div>
      
      {/* Global Activity Stream */}
      <div className="mt-6">
        <ResizablePane className="w-full min-h-[200px]">
          <div className="h-full bg-slate-900 border border-slate-600 rounded-lg overflow-hidden">
            <div className="p-3 border-b border-slate-600 bg-slate-800">
              <h4 className="text-sm font-medium text-white">Global Team Activity</h4>
              <div className="text-xs text-slate-400">Inter-LLM collaboration events</div>
            </div>
            <div className="flex-1 overflow-auto p-2 max-h-[300px]">
              {events.length === 0 ? (
                <div className="text-center text-slate-500 text-sm mt-8">
                  <div className="text-2xl mb-2">🤝</div>
                  <div>No team collaboration yet</div>
                  <div className="text-xs mt-1">LLMs will appear here when they collaborate</div>
                </div>
              ) : (
                events.map((event, i) => (
                  <div key={i} className="text-xs font-mono px-2 py-1 border-b border-slate-700">
                    <span className="text-slate-400">
                      [{new Date(event.ts * 1000).toLocaleTimeString()}]
                    </span>
                    <span className="ml-2 text-blue-300">{event.slot}</span>
                    <span className="ml-2 text-yellow-300">{event.event}</span>
                    {event.text && <span className="ml-2 text-slate-300">— {event.text.slice(0, 100)}...</span>}
                  </div>
                ))
              )}
            </div>
          </div>
        </ResizablePane>
      </div>
    </div>
  )
}
