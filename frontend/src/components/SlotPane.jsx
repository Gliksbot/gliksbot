import React, { useEffect, useState } from 'react';

export default function SlotPane({slot}){
  const [preview, setPreview] = useState('');
  const [configured, setConfigured] = useState(true);
  const [loading, setLoading] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(Date.now());
  
  const loadSlotData = () => {
    fetch(`/api/collaboration/head?slot=${slot}&n=1`)
      .then(r => r.ok ? r.json() : {items:[]})
      .then(d => {
        if (!d.items?.length) { 
          setConfigured(false); 
          setPreview('No recent activity');
          return; 
        }
        setConfigured(true);
        const latestItem = d.items[0];
        let displayText = latestItem.text || JSON.stringify(latestItem);
        
        // Truncate very long responses for preview
        if (displayText.length > 200) {
          displayText = displayText.substring(0, 200) + '...';
        }
        
        setPreview(displayText);
        setLastUpdate(Date.now());
      })
      .catch(() => {
        setConfigured(false);
        setPreview('Error loading data');
      });
  };
  
  useEffect(() => {
    loadSlotData();
    
    // Auto-refresh every 5 seconds
    const interval = setInterval(loadSlotData, 5000);
    return () => clearInterval(interval);
  }, [slot]);
  
  const sendUserInput = async () => {
    if (!userInput.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/collaboration/input/${slot}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userInput }),
      });
      
      const result = await response.json();
      if (result.success) {
        setUserInput('');
        setShowInput(false);
        // Refresh slot data to show the response
        setTimeout(loadSlotData, 1000);
      } else {
        alert('Error: ' + (result.error || 'Failed to send message'));
      }
    } catch (error) {
      alert('Error sending message: ' + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="border rounded p-2 h-40 overflow-hidden flex flex-col bg-slate-900">
      <div className="text-sm font-semibold flex items-center justify-between text-white">
        <span>{slot}</span>
        <div className="flex items-center space-x-2">
          {!configured && <span className="text-xs bg-red-600 px-2 py-0.5 rounded text-white">Not configured</span>}
          <button 
            onClick={loadSlotData}
            className="text-xs bg-slate-700 hover:bg-slate-600 px-2 py-0.5 rounded text-white"
            title="Refresh"
          >
            🔄
          </button>
          <button 
            onClick={() => setShowInput(!showInput)}
            className="text-xs bg-blue-600 hover:bg-blue-500 px-2 py-0.5 rounded text-white"
            title="Send message to this LLM"
          >
            💬
          </button>
        </div>
      </div>
      
      {showInput && (
        <div className="mt-2 mb-2">
          <div className="flex space-x-2">
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendUserInput()}
              placeholder="Type message to this LLM..."
              className="flex-1 text-xs px-2 py-1 bg-slate-800 border border-slate-600 rounded text-white placeholder-slate-400"
              disabled={loading}
            />
            <button
              onClick={sendUserInput}
              disabled={loading || !userInput.trim()}
              className="text-xs bg-green-600 hover:bg-green-500 disabled:bg-gray-600 px-2 py-1 rounded text-white"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </div>
      )}
      
      <div className="text-xs font-mono mt-1 overflow-auto whitespace-pre-wrap flex-1 text-slate-300">
        {preview || '…'}
      </div>
      
      <div className="flex justify-between mt-1">
        <button 
          className="text-xs underline text-blue-400 hover:text-blue-300" 
          onClick={() => window.open(`/api/collaboration/file?slot=${slot}`,'_blank')}
        >
          Open details
        </button>
        <span className="text-xs text-slate-500">
          Updated: {new Date(lastUpdate).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
