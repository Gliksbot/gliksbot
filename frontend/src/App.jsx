import React from 'react'
import Nav from './components/Nav.jsx'
import Normal from './pages/Normal.jsx'
import Models from './pages/Models.jsx'
import Memory from './pages/Memory.jsx'
import Patterns from './pages/Patterns.jsx'
import ConfigPage from './pages/Config.jsx'
import Downloads from './pages/Downloads.jsx'
import Campaigns from './pages/Campaigns.jsx'
import { api } from './api'
import { isAuthed, setToken } from './auth'

export default function App(){
  const [tab,setTab]=React.useState('normal')
  const [showLogin, setShowLogin] = React.useState(false)
  const [loginForm, setLoginForm] = React.useState({username: '', password: ''})
  const [loggingIn, setLoggingIn] = React.useState(false)
  
  const onLogin=async()=>{ 
    if (!loginForm.username || !loginForm.password) {
      alert('Please enter both username and password')
      return
    }
    
    setLoggingIn(true)
    try{ 
      const {data}=await api.post('/auth/login',{
        username: loginForm.username,
        password: loginForm.password
      })
      setToken(data.token)
      setShowLogin(false)
      setLoginForm({username: '', password: ''})
      alert('Logged in successfully!') 
    }catch(e){ 
      alert('Login failed: '+(e?.response?.data?.detail||e.message)) 
    } finally {
      setLoggingIn(false)
    }
  }
  
  const onLogout=()=>{ setToken(null); alert('Logged out.') }
  const guest=!isAuthed()
  
  return (
    <div className="min-h-screen">
      <Nav tab={tab} setTab={setTab} onShowLogin={() => setShowLogin(true)} onLogout={onLogout}/>
      
      {/* Login Modal */}
      {showLogin && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Login</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Username"
                value={loginForm.username}
                onChange={(e) => setLoginForm(prev => ({...prev, username: e.target.value}))}
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                disabled={loggingIn}
              />
              <input
                type="password"
                placeholder="Password"
                value={loginForm.password}
                onChange={(e) => setLoginForm(prev => ({...prev, password: e.target.value}))}
                className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2"
                disabled={loggingIn}
                onKeyPress={(e) => e.key === 'Enter' && onLogin()}
              />
              <div className="flex gap-2">
                <button
                  onClick={onLogin}
                  disabled={loggingIn || !loginForm.username || !loginForm.password}
                  className="flex-1 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded text-sm"
                >
                  {loggingIn ? 'Logging in...' : 'Login'}
                </button>
                <button
                  onClick={() => {
                    setShowLogin(false)
                    setLoginForm({username: '', password: ''})
                  }}
                  disabled={loggingIn}
                  className="flex-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {tab==='downloads' ? <Downloads/> :
       tab==='normal' ? <Normal/> :
       tab==='campaigns' && !guest ? <Campaigns/> :
       tab==='models' && !guest ? <Models/> :
       tab==='memory' && !guest ? <Memory/> :
       tab==='patterns' && !guest ? <Patterns/> :
       tab==='config' && !guest ? <ConfigPage/> :
       <div className="p-6 text-slate-400">This tab requires login.</div>}
    </div>
  )
}
