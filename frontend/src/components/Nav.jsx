import React from 'react'
import { isAuthed } from '../auth'

export default function Nav({ tab, setTab, onShowLogin, onLogout }){
  const guest = !isAuthed()
  const Tab = ({name,id,allowed=true}) => (
    <button 
      onClick={()=> allowed && setTab(id)} 
      className={`px-3 py-2 rounded-md text-sm font-medium ${
        tab===id?'bg-slate-800 text-white':'text-slate-300 hover:text-white'
      } ${allowed?'':'opacity-40 cursor-not-allowed'}`}
    >
      {name}
    </button>
  )
  
  return (
    <div className="w-full border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-3 py-2 flex items-center gap-2">
        <div className="text-lg font-semibold mr-4">Dexter v3</div>
        <Tab name="Normal" id="normal" allowed={true} />
        <Tab name="Campaigns" id="campaigns" allowed={!guest} />
        <Tab name="Models" id="models" allowed={!guest} />
        <Tab name="Memory" id="memory" allowed={!guest} />
        <Tab name="Patterns" id="patterns" allowed={!guest} />
        <Tab name="Config" id="config" allowed={!guest} />
        <Tab name="Downloads" id="downloads" allowed={true} />
        <div className="flex-1" />
        {guest ? (
          <button 
            onClick={onShowLogin} 
            className="px-3 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-md text-sm"
          >
            Login
          </button>
        ) : (
          <button 
            onClick={onLogout} 
            className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-md text-sm"
          >
            Logout
          </button>
        )}
      </div>
    </div>
  )
}
