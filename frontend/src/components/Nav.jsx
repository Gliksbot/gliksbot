import React from 'react'

export default function Nav({ tab, setTab }){
  const Tab = ({name,id}) => (
    <button 
      onClick={() => setTab(id)} 
      className={`px-3 py-2 rounded-md text-sm font-medium ${
        tab===id?'bg-slate-800 text-white':'text-slate-300 hover:text-white'
      }`}
    >
      {name}
    </button>
  )
  
  return (
    <div className="w-full border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-3 py-2 flex items-center gap-2">
        <div className="text-lg font-semibold mr-4">Dexter v3</div>
        <Tab name="Normal" id="normal" />
        <Tab name="Campaigns" id="campaigns" />
        <Tab name="Skills" id="skills" />
        <Tab name="Models" id="models" />
        <Tab name="Memory" id="memory" />
        <Tab name="Patterns" id="patterns" />
        <Tab name="Config" id="config" />
        <Tab name="Downloads" id="downloads" />
        <div className="flex-1" />
      </div>
    </div>
  )
}
