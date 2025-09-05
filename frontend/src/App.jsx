import React from 'react'
import Nav from './components/Nav.jsx'
import Normal from './pages/Normal.jsx'
import Models from './pages/Models.jsx'
import Memory from './pages/Memory.jsx'
import Patterns from './pages/Patterns.jsx'
import ConfigPage from './pages/Config.jsx'
import Downloads from './pages/Downloads.jsx'
import Campaigns from './pages/Campaigns.jsx'
import Skills from './pages/Skills.jsx'

export default function App(){
  const [tab,setTab]=React.useState('normal')
  
  return (
    <div className="min-h-screen">
      <Nav tab={tab} setTab={setTab}/>
      
      {tab==='downloads' ? <Downloads/> :
       tab==='normal' ? <Normal/> :
       tab==='campaigns' ? <Campaigns/> :
       tab==='skills' ? <Skills/> :
       tab==='models' ? <Models/> :
       tab==='memory' ? <Memory/> :
       tab==='patterns' ? <Patterns/> :
       tab==='config' ? <ConfigPage/> :
       <div className="p-6 text-slate-400">Unknown tab.</div>}
    </div>
  )
}
