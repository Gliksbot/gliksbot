import React, { useEffect, useState } from 'react';
export default function SlotPane({slot}){
  const [preview, setPreview] = useState('');
  const [configured, setConfigured] = useState(true);
  useEffect(() => {
    fetch(`/api/collaboration/head?slot=${slot}&n=1`).then(r=>r.ok?r.json():{items:[]}).then(d=>{
      if (!d.items?.length) { setConfigured(false); return; }
      setPreview(d.items[0].text || JSON.stringify(d.items[0]));
    }).catch(()=>setConfigured(false));
  }, [slot]);
  return (
    <div className="border rounded p-2 h-40 overflow-hidden flex flex-col">
      <div className="text-sm font-semibold flex items-center justify-between">
        <span>{slot}</span>
        {!configured && <span className="text-xs bg-gray-200 px-2 py-0.5 rounded">Not configured</span>}
      </div>
      <div className="text-xs font-mono mt-1 overflow-auto whitespace-pre-wrap flex-1">
        {preview || '…'}
      </div>
      <button className="mt-1 text-xs underline" onClick={()=>window.open(`/api/collaboration/file?slot=${slot}`,'_blank')}>Open details</button>
    </div>
  );
}
