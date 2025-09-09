import React from 'react'
import { NavLink } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext.jsx'

export default function Nav(){
  const { theme, toggleTheme } = useTheme()

  const Link = ({ name, to, shortcut }) => (
    <NavLink
      to={to}
      accessKey={shortcut}
      className={({ isActive }) =>
        `px-3 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring ${
          isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:text-white'
        }`
      }
    >
      {name}
    </NavLink>
  )

  return (
    <nav role="navigation" aria-label="Main" className="w-full border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-3 py-2 flex items-center gap-2">
        <div className="text-lg font-semibold mr-4">Dexter v3</div>
        <Link name="Normal" to="/" shortcut="n" />
        <Link name="Campaigns" to="/campaigns" shortcut="c" />
        <Link name="Skills" to="/skills" shortcut="s" />
        <Link name="Models" to="/models" shortcut="m" />
        <Link name="Memory" to="/memory" shortcut="y" />
        <Link name="Patterns" to="/patterns" shortcut="p" />
        <Link name="Config" to="/config" shortcut="g" />
        <Link name="Downloads" to="/downloads" shortcut="d" />
        <div className="flex-1" />
        <button
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="px-3 py-2 rounded-md text-sm font-medium text-slate-300 hover:text-white focus:outline-none focus:ring"
        >
          {theme === 'dark' ? '🌙' : '☀️'}
        </button>
      </div>
    </nav>
  )
}
