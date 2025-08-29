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
  const onLogin=async()=>{ 
    const username=prompt('AD Username (user or user@domain)')
    const password=prompt('AD Password')
    if(!username||!password) return
    try{ 
      const {data}=await api.post('/auth/login',{username,password})
      setToken(data.token)
      alert('Logged in.') 
    }catch(e){ 
      alert('Login failed: '+(e?.response?.data?.detail||e.message)) 
    } 
  }
  const onLogout=()=>{ setToken(null); alert('Logged out.') }
  const guest=!isAuthed()
  
  return (
    <div className="min-h-screen">
      <Nav tab={tab} setTab={setTab} onLogin={onLogin} onLogout={onLogout}/>
      {tab==='downloads' ? <Downloads/> :
       tab==='normal' ? <Normal/> :
       tab==='campaigns' && !guest ? <Campaigns/> :
       tab==='models' && !guest ? <Models/> :
       tab==='memory' && !guest ? <Memory/> :
       tab==='patterns' && !guest ? <Patterns/> :
       tab==='config' && !guest ? <ConfigPage/> :
       <div className="p-6 text-slate-400">This tab requires AD login.</div>}
    </div>
  )
}
