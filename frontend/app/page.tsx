'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Message, RAGContextHit, DatasetProfile, FilteredQueryOutput } from '@/types/chat';
import { ReasoningTrace } from '@/components/reasoning-trace';
import { ToolOutput } from '@/components/tool-output';

interface BackendChatResponse {
  answer: string;
  routing_meta: {
    track_selected: string;
    reasoning_trace: string;
    applied_filters: {
      column: string | null;
      operator: string | null;
      value: string | number | boolean | null;
    };
  };
  raw_payloads: {
    rag_context: RAGContextHit[] | null;
    tool_execution: DatasetProfile | FilteredQueryOutput | Record<string, unknown> | null;
  };
}

interface BackendUploadResponse {
  filename: string;
  indexing_results?: {
    indexed_elements: number;
  };
}

type PersonalityType = 'technical' | 'casual' | 'friendly' | 'minimalist';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  
  // 📂 Multi-file Storage States
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');

  // 🎭 Dynamic Engine Personality States
  const [personality, setPersonality] = useState<PersonalityType>('technical');
  const [temperature, setTemperature] = useState<number>(0.2);

  const [activeMeta, setActiveMeta] = useState<Message['routingMeta']>(undefined);
  const [activePayloads, setActivePayloads] = useState<Message['rawPayloads']>(undefined);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Synchronize past dialogue records and list available workspace files from backend core
  useEffect(() => {
    const syncHistoricalLogs = async () => {
      try {
        // Sync chat timeline logs
        const response = await fetch('http://127.0.0.1:8000/api/memory/history');
        if (response.ok) {
          const historyData = (await response.json()) as Message[];
          setMessages(historyData);
          
          const lastReiMsg = [...historyData].reverse().find(msg => msg.sender === 'rei');
          if (lastReiMsg?.routingMeta) {
            setActiveMeta(lastReiMsg.routingMeta);
            setActivePayloads(lastReiMsg.rawPayloads);
            setSelectedMessageId(lastReiMsg.id);
          }
        }

        // Fetch available active uploaded tracking datasets
        const filesResponse = await fetch('http://127.0.0.1:8000/api/files');
        if (filesResponse.ok) {
          const filesData = await filesResponse.json() as string[];
          setUploadedFiles(filesData);
          if (filesData.length > 0) {
            setSelectedFile(filesData[0]); // Default to first uploaded vector mount
          }
        }
      } catch (err) {
        console.error("Failed to restore conversational dashboard timeline:", err);
      }
    };
    
    syncHistoricalLogs();
  }, []);

  // Smooth scroll tracking container rule
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handlePersonalityChange = (tone: PersonalityType) => {
    setPersonality(tone);
    if (tone === 'technical') setTemperature(0.2);
    if (tone === 'casual') setTemperature(0.6);
    if (tone === 'friendly') setTemperature(0.8);
    if (tone === 'minimalist') setTemperature(0.1);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg: Message = {
      id: crypto.randomUUID(),
      sender: 'user',
      text: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMsg.text,
          config: {
            personality: personality,
            temperature: temperature,
            target_file: selectedFile || null // Injects target anchor into processing stream
          }
        }),
      });

      if (!response.ok) throw new Error('Network execution error from REI core.');
      const data = (await response.json()) as BackendChatResponse;

      const reiMsg: Message = {
        id: crypto.randomUUID(),
        sender: 'rei',
        text: data.answer,
        timestamp: new Date(),
        routingMeta: {
          trackSelected: data.routing_meta.track_selected,
          reasoningTrace: data.routing_meta.reasoning_trace,
          appliedFilters: data.routing_meta.applied_filters,
        },
        rawPayloads: {
          ragContext: data.raw_payloads.rag_context,
          toolExecution: data.raw_payloads.tool_execution,
        },
      };

      setMessages((prev) => [...prev, reiMsg]);
      setActiveMeta(reiMsg.routingMeta);
      setActivePayloads(reiMsg.rawPayloads);
      setSelectedMessageId(reiMsg.id);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          sender: 'rei',
          text: 'System Error: Connection to backend core interrupted. Ensure uvicorn is running on port 8000.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('File transfer failed.');
      const data = (await res.json()) as BackendUploadResponse;
      
      // Append new filename index tracking elements dynamically if missing
      setUploadedFiles((prev) => {
        if (prev.includes(data.filename)) return prev;
        return [...prev, data.filename];
      });
      setSelectedFile(data.filename); // Anchor system attention directly onto newly uploaded asset
      
      alert(`🎉 Dataset synchronized & indexed successfully:\n${data.filename}\nRecords found: ${data.indexing_results?.indexed_elements || 0}`);
    } catch (err) {
      console.error(err);
      alert('Error mounting target file. Make sure backend is live.');
    } finally {
      setUploading(false);
    }
  };

  const clearMemoryState = async () => {
    if (!confirm("Are you sure you want to completely wipe REI's persistent memory cores?")) return;
    try {
      const res = await fetch('http://127.0.0.1:8000/api/memory/clear', { method: 'POST' });
      if (res.ok) {
        setMessages([]);
        setActiveMeta(undefined);
        setActivePayloads(undefined);
        setSelectedMessageId(null);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const getTrackColorStyle = (track?: string) => {
    if (!track) return 'border-zinc-900/80 hover:border-zinc-800/80';
    switch (track.toUpperCase()) {
      case 'RAG': return 'border-emerald-500/20 bg-[#0a1410]/40 text-emerald-100 hover:border-emerald-500/40';
      case 'TOOL': return 'border-violet-500/20 bg-[#120f1a]/40 text-violet-100 hover:border-violet-500/40';
      case 'HYBRID': return 'border-cyan-500/20 bg-[#0f161a]/40 text-cyan-100 hover:border-cyan-500/40';
      default: return 'border-zinc-800/80 bg-[#111116]/40 text-zinc-300 hover:border-zinc-700/80';
    }
  };

  return (
    <main className="h-screen bg-[#070709] text-zinc-100 flex flex-col overflow-hidden relative selection:bg-emerald-500/30 selection:text-emerald-300 antialiased font-mono">
      <div className="absolute inset-0 bg-[radial-gradient(#1c1c24_1px,transparent_1px)] bg-size:[16px_16px] opacity-10 pointer-events-none" />

      {/* Top Banner Header */}
      <header className="border-b border-zinc-800/60 px-6 py-3 flex items-center justify-between bg-[#0b0b0f]/80 backdrop-blur-xl z-50 shrink-0 shadow-[0_1px_10px_rgba(0,0,0,0.8)] relative">
        <div className="flex items-center space-x-4">
          <div className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500 shadow-[0_0_8px_#10b981]"></span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-bold font-mono tracking-[0.2em] text-zinc-200">REI SYSTEM // V2.5 CORE</span>
            <span className="text-[9px] text-zinc-500 font-mono tracking-wider uppercase">Contextual Memory Architecture</span>
          </div>
        </div>

        {/* Context Stream Selector Block */}
        <div className="flex items-center space-x-2 bg-zinc-950/80 px-3 py-1 rounded-xl border border-zinc-900">
          <span className="text-[9px] text-zinc-500 tracking-widest font-bold uppercase">TARGET FRAME:</span>
          {uploadedFiles.length === 0 ? (
            <span className="text-[10px] text-zinc-600 italic px-2">No contexts mounted</span>
          ) : (
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="bg-zinc-900 border border-zinc-800 rounded px-2 py-0.5 text-[10px] font-bold text-emerald-400 focus:outline-none focus:border-emerald-500/50 cursor-pointer min-w-35"
            >
              {uploadedFiles.map((filename) => (
                <option key={filename} value={filename} className="bg-zinc-950 text-zinc-300">
                  {filename}
                </option>
              ))}
            </select>
          )}
        </div>
        
        {/* Actions Cluster Panel */}
        <div className="flex items-center space-x-3">
          <button 
            type="button"
            onClick={clearMemoryState}
            className="text-[10px] tracking-wider text-zinc-500 hover:text-rose-400 border border-zinc-800/60 hover:border-rose-500/20 bg-zinc-900/40 hover:bg-rose-500/5 px-3 py-1.5 rounded-lg transition-all active:scale-95 uppercase"
          >
             Clear Cache
          </button>
          <label className="text-[10px] tracking-wider bg-zinc-900/60 hover:bg-zinc-800 text-zinc-300 hover:text-emerald-400 active:scale-95 transition-all px-4 py-1.5 rounded-lg border border-zinc-800 cursor-pointer flex items-center space-x-2 select-none group shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
            <span className="group-hover:animate-pulse">{uploading ? '⚡ SYSTEM MOUNTING...' : '📂 SYNC RECON DATA'}</span>
            <input type="file" accept=".csv,.txt" onChange={handleFileUpload} className="hidden" disabled={uploading} />
          </label>
        </div>
      </header>

      {/* Main Multi-Pane Dashboard Layout */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Side: Advanced Cyber Chat Feed Interface */}
        <div className="w-7/12 flex flex-col bg-[#08080c] relative">
          <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 my-auto space-y-4 max-w-md mx-auto border border-dashed border-zinc-800/40 rounded-2xl bg-zinc-900/5 backdrop-blur-sm">
                <div className="w-12 h-12 rounded-xl bg-zinc-900/60 border border-zinc-800 flex items-center justify-center text-zinc-500 text-lg shadow-inner">⚡</div>
                <div className="space-y-1">
                  <p className="text-zinc-400 text-xs font-bold uppercase tracking-widest">Awaiting Active Streams</p>
                  <p className="text-zinc-600 text-[11px] leading-relaxed font-sans">
                    Core models are stabilized. Mount a workspace CSV above to initiate automated frame vectors, or ask conversational pipeline commands directly.
                  </p>
                </div>
              </div>
            )}
            
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              const isSelected = selectedMessageId === msg.id;
              const trackType = msg.routingMeta?.trackSelected;
              
              return (
                <div
                  key={msg.id}
                  onClick={() => {
                    if (msg.routingMeta) {
                      setActiveMeta(msg.routingMeta);
                      setActivePayloads(msg.rawPayloads);
                      setSelectedMessageId(msg.id);
                    }
                  }}
                  className={`flex flex-col space-y-2 group transition-all duration-200 cursor-pointer ${isUser ? 'items-end' : 'items-start'}`}
                >
                  {/* Dynamic Header Badge labels per turn */}
                  <div className="flex items-center space-x-2 text-[10px] tracking-widest text-zinc-600 uppercase px-2">
                    <span>{isUser ? '◆ Operator' : `◇ REI Intelligence ${trackType ? `// [${trackType}]` : ''}`}</span>
                    {!isUser && msg.routingMeta && (
                      <span className={`text-[9px] px-1.5 py-0.2 rounded border transition-all ${
                        isSelected 
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                          : 'opacity-0 group-hover:opacity-100 bg-zinc-900 border-zinc-800 text-zinc-400'
                      }`}>
                        {isSelected ? 'ACTIVE STREAM' : 'INSPECT TRACK'}
                      </span>
                    )}
                  </div>

                  {/* Chat Bubbles styled to resemble clean structural blocks */}
                  <div
                    className={`max-w-[90%] p-4 rounded-xl text-xs leading-relaxed transition-all relative border font-sans ${
                      isUser
                        ? 'bg-[#12121a] text-zinc-200 border-zinc-800 shadow-[0_4px_12px_rgba(0,0,0,0.4)]'
                        : `${getTrackColorStyle(trackType)} ${isSelected ? 'ring-1 ring-zinc-700 shadow-md' : ''}`
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{msg.text}</div>
                  </div>
                </div>
              );
            })}
            
            {loading && (
              <div className="flex flex-col space-y-2 items-start animate-pulse">
                <div className="text-[10px] tracking-widest text-zinc-600 uppercase px-2">◇ REI Intelligence</div>
                <div className="bg-zinc-900/30 text-zinc-500 border border-zinc-800/40 px-4 py-3 rounded-xl text-[11px] tracking-wider font-mono">
                  [REI_CORE] // RUNNING ROUTER INFERENCE ON {selectedFile || 'SYSTEM_BASE'} VIA {personality.toUpperCase()} DIRECTIVE...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Form Message Input Console Bar */}
          <form onSubmit={handleSendMessage} className="p-4 border-t border-zinc-900/80 bg-[#09090d]/90 backdrop-blur-md shrink-0 relative space-y-3">
            
            {/* Dynamic Personality Configuration Bar */}
            <div className="flex items-center justify-between bg-[#0b0b10] border border-zinc-900 px-3 py-2 rounded-xl text-[10px]">
              <div className="flex items-center space-x-1.5 text-zinc-500">
                <span>CONFIG:</span>
                <span className="text-zinc-300 font-bold uppercase tracking-wider">{personality}</span>
                <span className="text-zinc-600">|</span>
                <span>TEMP:</span>
                <span className="text-zinc-400">{temperature.toFixed(1)}</span>
              </div>
              <div className="flex items-center space-x-1 bg-zinc-950 p-0.5 rounded-lg border border-zinc-900/60">
                {(['technical', 'casual', 'friendly', 'minimalist'] as PersonalityType[]).map((tone) => (
                  <button
                    key={tone}
                    type="button"
                    onClick={() => handlePersonalityChange(tone)}
                    className={`px-2.5 py-1 rounded-md tracking-wider uppercase text-[9px] font-bold transition-all ${
                      personality === tone
                        ? 'bg-zinc-800 text-zinc-100 border border-zinc-700/50 shadow-inner'
                        : 'text-zinc-600 hover:text-zinc-400 hover:bg-zinc-900/50'
                    }`}
                  >
                    {tone}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center space-x-3 bg-[#050507] border border-zinc-850 focus-within:border-zinc-700 p-1.5 rounded-xl transition-all shadow-[inset_0_2px_4px_rgba(0,0,0,0.6)]">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={selectedFile ? `QUERY MOUNTED DATASET [${selectedFile}]...` : "PROMPT RECON CONFIGURATION RANGE OR COMMAND REQUEST..."}
                className="flex-1 bg-transparent px-4 py-2 text-xs font-mono tracking-wider focus:outline-none text-zinc-200 placeholder-zinc-700 disabled:opacity-40"
                disabled={loading}
              />
              <button
                type="submit"
                className="bg-zinc-100 hover:bg-zinc-200 text-zinc-950 active:scale-95 font-mono font-bold text-[10px] tracking-widest px-4 py-2.5 rounded-lg transition-all disabled:opacity-20 disabled:scale-100 shadow-[0_2px_8px_rgba(255,255,255,0.1)]"
                disabled={loading || !input.trim()}
              >
                EXEC
              </button>
            </div>
          </form>
        </div>

        {/* Right Side: The Observability Suite Panels */}
        <div className="w-5/12 p-6 bg-[#060609] overflow-y-auto space-y-6 border-l border-zinc-900/60 scrollbar-thin scrollbar-thumb-zinc-900 scrollbar-track-transparent">
          <div>
            <div className="flex items-center justify-between border-b border-zinc-900 pb-2 mb-3">
              <h2 className="text-[10px] font-bold tracking-[0.25em] text-zinc-500 uppercase">Observability Metrics</h2>
              <div className="text-[9px] text-zinc-600 px-1.5 py-0.5 rounded border border-zinc-900 bg-zinc-950">NODE_01</div>
            </div>
            <ReasoningTrace meta={activeMeta} />
          </div>
          <div>
            <div className="flex items-center justify-between border-b border-zinc-900 pb-2 mb-3">
              <h2 className="text-[10px] font-bold tracking-[0.25em] text-zinc-500 uppercase">Context Inspection</h2>
              <div className="text-[9px] text-zinc-600 px-1.5 py-0.5 rounded border border-zinc-900 bg-zinc-950">PAYLOAD_BUFFER</div>
            </div>
            <ToolOutput payloads={activePayloads} />
          </div>
        </div>
      </div>
    </main>
  );
}