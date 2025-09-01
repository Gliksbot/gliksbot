import React, { useEffect, useRef, useState } from 'react';
export default function ActivityStream() {
  const [events, setEvents] = useState([]);
  const [paused, setPaused] = useState(false);
  const bottomRef = useRef(null);
  useEffect(() => {
    const es = new EventSource('/api/events');
    es.onmessage = (m) => {
      if (paused) return;
      try { const e = JSON.parse(m.data); setEvents(prev => [...prev.slice(-9999), e]); } catch {}
    };
    es.onerror = () => { /* TODO: show banner */ };
    return () => es.close();
  }, [paused]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [events]);
  return (
    <div className="h-full overflow-auto">
      {events.map((e, i) => (
        <div key={i} className="text-xs font-mono px-2 py-1 border-b">
          {e.source === 'stub' && (<span className="px-1 mr-2 bg-yellow-200 text-yellow-900 rounded">FAKE</span>)}
          <span>[{new Date(e.ts*1000).toLocaleTimeString()}]</span>
          <span className="ml-2">{e.slot}</span>
          <span className="ml-2">{e.event}</span>
          {e.text && <span className="ml-2">— {e.text}</span>}
        </div>
      ))}
      <div ref={bottomRef} />
      <div className="p-2 border-t flex gap-2">
        <button onClick={() => setPaused(p => !p)} className="px-2 py-1 border rounded">{paused ? 'Resume' : 'Pause'}</button>
        <button onClick={async ()=>{
          try{
            await fetch('/api/events/ping', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({slot:'dexter', event:'ui.ping', text:'Hello from UI'})});
          }catch(e){ console.error('ping failed', e); }
        }} className="px-2 py-1 border rounded">Ping</button>
      </div>
    </div>
  );
}
