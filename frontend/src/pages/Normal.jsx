import { useState, useEffect } from 'react'
import ResizableGrid from '../components/ResizableGrid'

export default function Normal() {
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    // Simple ready check
    const timer = setTimeout(() => setIsReady(true), 100)
    return () => clearTimeout(timer)
  }, [])

  if (!isReady) {
    return (
      <div className="h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="text-4xl mb-4">🤖</div>
          <div className="text-xl text-white">Initializing LLM Team Interface...</div>
          <div className="text-sm text-slate-400 mt-2">Preparing individual LLM management boxes</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen bg-slate-950">
      <ResizableGrid />
    </div>
  )
}