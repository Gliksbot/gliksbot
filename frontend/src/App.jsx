import React from 'react'
import { Routes, Route } from 'react-router-dom'
import Nav from './components/Nav.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import Normal from './pages/Normal.jsx'
import Models from './pages/Models.jsx'
import Memory from './pages/Memory.jsx'
import Patterns from './pages/Patterns.jsx'
import ConfigPage from './pages/Config.jsx'
import Downloads from './pages/Downloads.jsx'
import Campaigns from './pages/Campaigns.jsx'
import Skills from './pages/Skills.jsx'

export default function App(){
  return (
    <div className="min-h-screen">
      <a href="#main" className="sr-only focus:not-sr-only">Skip to content</a>
      <Nav />
      <ErrorBoundary>
        <main id="main">
          <Routes>
            <Route path="/" element={<Normal/>} />
            <Route path="/campaigns" element={<Campaigns/>} />
            <Route path="/skills" element={<Skills/>} />
            <Route path="/models" element={<Models/>} />
            <Route path="/memory" element={<Memory/>} />
            <Route path="/patterns" element={<Patterns/>} />
            <Route path="/config" element={<ConfigPage/>} />
            <Route path="/downloads" element={<Downloads/>} />
            <Route path="*" element={<div className="p-6 text-slate-400">Unknown tab.</div>} />
          </Routes>
        </main>
      </ErrorBoundary>
    </div>
  )
}
