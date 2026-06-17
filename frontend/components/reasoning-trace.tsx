import React from 'react';

interface ReasoningTraceProps {
  meta?: {
    trackSelected: string;
    reasoningTrace: string;
    appliedFilters: {
      column: string | null;
      operator: string | null;
      value: string | number | boolean | null;
    };
  };
}

export const ReasoningTrace: React.FC<ReasoningTraceProps> = ({ meta }) => {
  if (!meta) {
    return (
      <div className="h-48 flex items-center justify-center text-zinc-500 text-sm italic p-4 bg-zinc-900/50 rounded-xl border border-zinc-800">
        Awaiting input to generate reasoning metrics...
      </div>
    );
  }

  const trackColors: Record<string, string> = {
    DIRECT: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    RAG: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    TOOL: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    HYBRID: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  };

  return (
    <div className="space-y-4 p-4 bg-zinc-900 rounded-xl border border-zinc-800">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider">REI Execution Trace</h3>
        <span className={`text-xs font-mono px-2 py-0.5 rounded border ${trackColors[meta.trackSelected] || 'bg-zinc-800 text-zinc-400'}`}>
          TRACK: {meta.trackSelected}
        </span>
      </div>
      
      <div className="text-sm text-zinc-300 bg-zinc-950 p-3 rounded-lg border border-zinc-850 font-mono leading-relaxed whitespace-pre-wrap">
        {meta.reasoningTrace}
      </div>

      {meta.appliedFilters.column && (
        <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-850 space-y-1">
          <div className="text-xs font-semibold text-zinc-400">Extracted Filter Matrix</div>
          <div className="text-xs font-mono text-amber-400">
            {meta.appliedFilters.column} {meta.appliedFilters.operator} {String(meta.appliedFilters.value)}
          </div>
        </div>
      )}
    </div>
  );
};