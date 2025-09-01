import React from 'react';
import SlotPane from './SlotPane';
const SLOTS = ['dexter','analyst','engineer','researcher','creative','validator','specialist1','specialist2'];
export default function SlotGrid(){
  return (
    <div className="grid grid-cols-2 gap-2 p-2 overflow-auto h-full">
      {SLOTS.map(s => <SlotPane key={s} slot={s} />)}
    </div>
  );
}

