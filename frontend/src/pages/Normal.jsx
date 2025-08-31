import React, { useState, useEffect, useRef } from 'react'
import { api } from '../api'

export default function Normal() {
  const [request, setRequest] = useState('')
  const [loading, setLoading] = useState(false)
  const [chatHistory, setChatHistory] = useState([])
  const [isListening, setIsListening] = useState(false)
  const [userMuted, setUserMuted] = useState(false)
  const [dexterMuted, setDexterMuted] = useState(false)
  const [models, setModels] = useState({})
  const [collaborationFiles, setCollaborationFiles] = useState({})
  const [selectedModel, setSelectedModel] = useState('')
  const [selectedFile, setSelectedFile] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [collaborationActive, setCollaborationActive] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [error, setError] = useState('')
  
  const recognitionRef = useRef(null)
  const synthRef = useRef(null)
  const chatContainerRef = useRef(null)

  useEffect(() => {
    loadChatHistory()
    loadModels()
    loadCollaborationFiles()
    initializeSpeech()
    
    // Set up auto-refresh for collaboration
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadModels()
        loadCollaborationFiles()
      }
    }, 3000)
    
    return () => clearInterval(interval)
  }, [autoRefresh])

  useEffect(() => {
    // Auto-scroll chat to bottom
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatHistory])

  useEffect(() => {
    // Load file content when file is selected
    if (selectedFile && selectedModel) {
      loadFileContent(selectedModel, selectedFile)
    }
  }, [selectedFile, selectedModel])

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

  const loadModels = async () => {
    try {
      const { data } = await api.get('/config')
      setModels(data?.models || {})
      
      // Check if any models are currently active
      const active = Object.values(data?.models || {}).some(model => model.enabled)
      setCollaborationActive(active)
    } catch (error) {
      console.error('Failed to load models:', error)
      setError('Failed to load model configuration')
    }
  }

  const loadCollaborationFiles = async () => {
    try {
      const { data } = await api.get('/collaboration/files')
      setCollaborationFiles(data || {})
    } catch (error) {
      console.error('Failed to load collaboration files:', error)
    }
  }

  const loadFileContent = async (modelName, fileName) => {
    try {
      const { data } = await api.get(`/collaboration/files/${modelName}/${fileName}`)
      setFileContent(data?.content || 'File is empty or could not be loaded')
    } catch (error) {
      console.error('Failed to load file content:', error)
      setFileContent('Error loading file: ' + error.message)
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
    setError('')
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
        timestamp: new Date().toISOString(),
        metadata: data.metadata || {}
      }
      setChatHistory(prev => [...prev, responseMessage])
      
      // Speak the response
      speakResponse(responseMessage.content)
      
      // Refresh collaboration data
      loadModels()
      loadCollaborationFiles()
      
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Error: ' + (error?.response?.data?.detail || error.message),
        timestamp: new Date().toISOString()
      }
      setChatHistory(prev => [...prev, errorMessage])
      setError(error?.response?.data?.detail || error.message)
    } finally {
      setLoading(false)
    }
  }

  const clearChat = () => {
    setChatHistory([])
  }

  const getModelStatus = (model) => {
    if (!model.enabled) return { status: 'disabled', color: 'gray', text: 'Disabled' }
    if (!model.provider) return { status: 'error', color: 'red', text: 'No Provider Configured' }
    if (!model.model) return { status: 'error', color: 'red', text: 'No Model Specified' }
    if (!model.api_key_env && !model.local_model) return { status: 'error', color: 'red', text: 'Missing API Key' }
    if (!model.endpoint && !model.local_model) return { status: 'error', color: 'red', text: 'No Endpoint URL' }
    return { status: 'active', color: 'green', text: 'Ready' }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  return (
    <div className="p-6 max-w-[100vw] mx-auto h-screen flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Chat with Dexter</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3 py-1 rounded text-sm ${
              autoRefresh ? 'bg-green-600 text-white' : 'bg-slate-600 text-slate-300'
            }`}
          >
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400">Collaboration:</span>
            <div className={`w-3 h-3 rounded-full ${collaborationActive ? 'bg-green-400' : 'bg-slate-600'}`}></div>
            <span className="text-sm">{collaborationActive ? 'Active' : 'Inactive'}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/50 border border-red-600 rounded-lg text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Configuration Warning */}
      {Object.values(models).some(model => {
        const status = getModelStatus(model)
        return model.enabled && status.status === 'error'
      }) && (
        <div className="mb-4 p-4 bg-yellow-900/50 border border-yellow-600 rounded-lg text-yellow-200">
          <div className="font-medium mb-2">⚠ Configuration Issues Detected</div>
          <div className="text-sm">
            Some AI models have configuration errors. Please check the Models tab to fix:
            <ul className="mt-2 list-disc list-inside">
              {Object.entries(models).filter(([name, model]) => {
                const status = getModelStatus(model)
                return model.enabled && status.status === 'error'
              }).map(([name, model]) => {
                const status = getModelStatus(model)
                return (
                  <li key={name} className="capitalize">
                    {name}: {status.text}
                  </li>
                )
              })}
            </ul>
          </div>
        </div>
      )}
      
      <div className="flex-1 flex gap-6 min-h-0">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Chat History */}
          <div 
            ref={chatContainerRef}
            className="flex-1 border border-slate-600 rounded-lg p-4 bg-slate-800/50 overflow-y-auto mb-4"
          >
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-600">
              <h2 className="text-lg font-semibold">Conversation</h2>
              <button
                onClick={clearChat}
                className="px-3 py-1 bg-slate-600 hover:bg-slate-500 rounded text-sm"
              >
                Clear Chat
              </button>
            </div>
            <div className="space-y-4">
              {chatHistory.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-4 rounded-lg shadow-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : message.type === 'error'
                      ? 'bg-red-600 text-white'
                      : 'bg-slate-700 text-slate-100'
                  }`}>
                    <div className="text-xs opacity-80 mb-2 flex justify-between items-center">
                      <span>{message.type === 'user' ? 'You' : message.type === 'error' ? 'System Error' : 'Dexter'}</span>
                      <span>{formatTimestamp(message.timestamp)}</span>
                    </div>
                    <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                    {message.metadata && Object.keys(message.metadata).length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-500/50 text-xs opacity-70">
                        <div>Models involved: {message.metadata.models_used?.join(', ') || 'None'}</div>
                        {message.metadata.collaboration_files && (
                          <div>Files created: {message.metadata.collaboration_files.length}</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-slate-700 text-slate-200 p-4 rounded-lg shadow-lg">
                    <div className="text-xs opacity-70 mb-2">Dexter is processing your request...</div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chat Input */}
          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={request}
                onChange={(e) => setRequest(e.target.value)}
                placeholder="Type your message to Dexter..."
                className="w-full bg-slate-700 border border-slate-600 rounded-lg p-3 pr-12 text-white placeholder-slate-400"
                disabled={loading}
              />
              <button
                type="button"
                onClick={toggleListening}
                disabled={userMuted || !recognitionRef.current}
                className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded ${
                  isListening 
                    ? 'bg-red-600 text-white' 
                    : 'bg-slate-600 hover:bg-slate-500 text-slate-300'
                } disabled:opacity-50`}
                title="Voice input"
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
              title="Toggle voice input"
            >
              {userMuted ? '🔇' : '🎤'}
            </button>
            
            <button
              type="button"
              onClick={() => setDexterMuted(!dexterMuted)}
              className={`px-3 py-2 rounded ${
                dexterMuted 
                  ? 'bg-red-600 text-white' 
                  : 'bg-slate-600 hover:bg-slate-500 text-slate-300'
              }`}
              title="Toggle Dexter's voice"
            >
              {dexterMuted ? '🔇' : '🔊'}
            </button>

            <button
              type="submit"
              disabled={loading || !request.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium text-white"
            >
              {loading ? 'Processing...' : 'Send'}
            </button>
          </form>
        </div>

        {/* Collaboration Panel */}
        <div className="w-[500px] flex flex-col">
          <h2 className="text-xl font-semibold mb-4">Team Collaboration</h2>
          
          {/* Models Status */}
          <div className="mb-6">
            <h3 className="text-lg font-medium mb-3">Active Models</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {Object.entries(models).map(([modelName, modelConfig]) => {
                const status = getModelStatus(modelConfig)
                return (
                  <div
                    key={modelName}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedModel === modelName 
                        ? 'border-blue-500 bg-blue-900/30' 
                        : status.status === 'error'
                        ? 'border-red-500 bg-red-900/20 hover:bg-red-800/30'
                        : status.status === 'disabled'
                        ? 'border-gray-500 bg-gray-900/20 hover:bg-gray-800/30'
                        : 'border-slate-600 bg-slate-800/30 hover:bg-slate-700/50'
                    }`}
                    onClick={() => setSelectedModel(modelName)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-medium capitalize">{modelName}</span>
                        <span className={`w-2 h-2 rounded-full bg-${status.color}-400`}></span>
                      </div>
                      <span className="text-xs text-slate-400">{modelConfig.role || 'No role'}</span>
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      {modelConfig.provider || 'No provider'} | {modelConfig.model || 'No model'}
                      {status.status === 'error' && (
                        <div className="text-red-400 mt-1 font-medium">
                          ⚠ {status.text}
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Collaboration Files */}
          <div className="flex-1 flex flex-col">
            <h3 className="text-lg font-medium mb-3">Collaboration Files</h3>
            
            {selectedModel && (
              <div className="mb-4 p-3 bg-slate-800/50 rounded-lg">
                <div className="text-sm font-medium mb-2">Files for: {selectedModel}</div>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {collaborationFiles[selectedModel]?.map((file) => (
                    <div
                      key={file.name}
                      className={`p-2 rounded cursor-pointer text-sm transition-all ${
                        selectedFile === file.name
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                      }`}
                      onClick={() => setSelectedFile(file.name)}
                    >
                      <div className="flex justify-between items-center">
                        <span>{file.name}</span>
                        <span className="text-xs opacity-70">
                          {formatFileSize(file.size)}
                        </span>
                      </div>
                      <div className="text-xs opacity-70">
                        {formatTimestamp(file.modified)}
                      </div>
                    </div>
                  )) || (
                    <div className="text-slate-400 text-sm text-center py-4">
                      {selectedModel === 'dexter' && getModelStatus(models.dexter)?.status === 'error' 
                        ? 'Dexter is not configured properly. Check the Models tab.' 
                        : 'No collaboration files yet. Send a message to start AI collaboration.'}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* File Content Viewer */}
            {selectedFile && selectedModel && (
              <div className="flex-1 flex flex-col border border-slate-600 rounded-lg bg-slate-800/30">
                <div className="p-3 border-b border-slate-600 bg-slate-700/50">
                  <div className="text-sm font-medium">{selectedFile}</div>
                  <div className="text-xs text-slate-400">Model: {selectedModel}</div>
                </div>
                <div className="flex-1 p-3 overflow-auto">
                  <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                    {fileContent}
                  </pre>
                </div>
              </div>
            )}

            {!selectedModel && (
              <div className="flex-1 flex items-center justify-center text-slate-400 text-center">
                <div>
                  <div className="text-4xl mb-2">📁</div>
                  <div>Select a model to view collaboration files</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
