import React from 'react'
import { api } from '../api'

export default function Skills() {
  const [skills, setSkills] = React.useState([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState(null)
  const [selectedSkill, setSelectedSkill] = React.useState(null)
  const [testMessage, setTestMessage] = React.useState('hello world')
  const [testResult, setTestResult] = React.useState(null)
  const [testing, setTesting] = React.useState(false)

  React.useEffect(() => {
    loadSkills()
  }, [])

  const loadSkills = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.get('/skills')
      setSkills(data.items || [])
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Failed to load skills')
    } finally {
      setLoading(false)
    }
  }

  const testSkill = async (skillId) => {
    setTesting(true)
    setTestResult(null)
    try {
      const { data } = await api.post(`/skills/${skillId}/test`)
      setTestResult({ success: true, data })
    } catch (e) {
      setTestResult({ 
        success: false, 
        error: e?.response?.data?.detail || e.message || 'Test failed' 
      })
    } finally {
      setTesting(false)
    }
  }

  const promoteSkill = async (skillId) => {
    try {
      const { data } = await api.post(`/skills/${skillId}/promote`)
      alert('Skill promoted successfully!')
      loadSkills() // Reload to get updated status
    } catch (e) {
      alert('Failed to promote skill: ' + (e?.response?.data?.detail || e.message))
    }
  }

  const executeSkill = async (skillId) => {
    try {
      const { data } = await api.post(`/skills/${skillId}/execute`, { message: testMessage })
      setTestResult({ success: true, execution: data })
    } catch (e) {
      setTestResult({ 
        success: false, 
        error: e?.response?.data?.detail || e.message || 'Execution failed' 
      })
    }
  }

  if (loading) return (
    <div className="p-6 text-slate-400">Loading skills...</div>
  )

  if (error) return (
    <div className="p-6">
      <div className="text-red-400 mb-4">Error: {error}</div>
      <button 
        onClick={loadSkills}
        className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-sm"
      >
        Retry
      </button>
    </div>
  )

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Skills Manager</h1>
        <button 
          onClick={loadSkills}
          className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm"
        >
          Refresh
        </button>
      </div>

      {skills.length === 0 ? (
        <div className="text-slate-400 text-center py-12">
          No skills found. Skills will appear here as they are created and tested.
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Skills List */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-white mb-4">Available Skills</h2>
            {skills.map((skill) => (
              <div 
                key={skill.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedSkill?.id === skill.id 
                    ? 'border-emerald-500 bg-slate-800/50' 
                    : 'border-slate-700 bg-slate-900/30 hover:border-slate-600'
                }`}
                onClick={() => setSelectedSkill(skill)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-white">{skill.name}</h3>
                  <span className={`px-2 py-1 rounded text-xs ${
                    skill.status === 'active' ? 'bg-green-600 text-white' :
                    skill.status === 'draft' ? 'bg-yellow-600 text-white' :
                    skill.status === 'failed' ? 'bg-red-600 text-white' :
                    'bg-slate-600 text-white'
                  }`}>
                    {skill.status}
                  </span>
                </div>
                {skill.description && (
                  <p className="text-slate-300 text-sm mb-2">{skill.description}</p>
                )}
                <div className="flex items-center gap-4 text-xs text-slate-400">
                  <span>Version: {skill.version}</span>
                  <span>Used: {skill.usage_count || 0}x</span>
                  <span>Success: {Math.round((skill.success_rate || 0) * 100)}%</span>
                </div>
              </div>
            ))}
          </div>

          {/* Skill Details & Testing */}
          <div className="space-y-4">
            {selectedSkill ? (
              <>
                <h2 className="text-lg font-semibold text-white">Skill Details</h2>
                <div className="p-4 border border-slate-700 rounded-lg bg-slate-900/30">
                  <h3 className="font-medium text-white mb-2">{selectedSkill.name}</h3>
                  {selectedSkill.description && (
                    <p className="text-slate-300 mb-4">{selectedSkill.description}</p>
                  )}
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Status:</span>
                      <span className="text-white">{selectedSkill.status}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Version:</span>
                      <span className="text-white">{selectedSkill.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Usage Count:</span>
                      <span className="text-white">{selectedSkill.usage_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Success Rate:</span>
                      <span className="text-white">{Math.round((selectedSkill.success_rate || 0) * 100)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Last Updated:</span>
                      <span className="text-white">
                        {new Date(selectedSkill.updated_ts * 1000).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-2">
                    {selectedSkill.status === 'draft' && (
                      <>
                        <button 
                          onClick={() => testSkill(selectedSkill.id)}
                          disabled={testing}
                          className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded text-sm"
                        >
                          {testing ? 'Testing...' : 'Test Skill'}
                        </button>
                        <button 
                          onClick={() => promoteSkill(selectedSkill.id)}
                          className="px-3 py-2 bg-green-600 hover:bg-green-500 rounded text-sm"
                        >
                          Promote to Active
                        </button>
                      </>
                    )}
                    {selectedSkill.status === 'active' && (
                      <button 
                        onClick={() => executeSkill(selectedSkill.id)}
                        className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-sm"
                      >
                        Execute Skill
                      </button>
                    )}
                  </div>
                </div>

                {/* Test Input */}
                <div className="p-4 border border-slate-700 rounded-lg bg-slate-900/30">
                  <h3 className="font-medium text-white mb-2">Test Input</h3>
                  <input 
                    type="text"
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    placeholder="Enter test message..."
                    className="w-full p-2 bg-slate-800 border border-slate-600 rounded text-white text-sm"
                  />
                </div>

                {/* Test Results */}
                {testResult && (
                  <div className="p-4 border border-slate-700 rounded-lg bg-slate-900/30">
                    <h3 className="font-medium text-white mb-2">Test Results</h3>
                    <div className={`p-3 rounded text-sm ${
                      testResult.success ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'
                    }`}>
                      {testResult.success ? (
                        <div>
                          <div className="font-medium mb-1">✓ Success</div>
                          {testResult.execution && (
                            <pre className="text-xs">{JSON.stringify(testResult.execution, null, 2)}</pre>
                          )}
                          {testResult.data && (
                            <div className="text-xs">Run ID: {testResult.data.run_id}</div>
                          )}
                        </div>
                      ) : (
                        <div>
                          <div className="font-medium mb-1">✗ Failed</div>
                          <div className="text-xs">{testResult.error}</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-slate-400 text-center py-12">
                Select a skill to view details and test it
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}