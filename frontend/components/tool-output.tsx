import React from 'react';
import { RAGContextHit, DatasetProfile, FilteredQueryOutput } from '@/types/chat';

interface ToolOutputProps {
  payloads?: {
    ragContext: RAGContextHit[] | null;
    toolExecution: DatasetProfile | FilteredQueryOutput | Record<string, unknown> | null;
  };
}

export const ToolOutput: React.FC<ToolOutputProps> = ({ payloads }) => {
  if (!payloads || (!payloads.ragContext && !payloads.toolExecution)) {
    return (
      <div className="h-48 flex items-center justify-center text-zinc-500 text-sm italic p-4 bg-zinc-900/50 rounded-xl border border-zinc-800">
        No active tool runtime state mounted.
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 bg-zinc-900 rounded-xl border border-zinc-800 max-h-125 overflow-y-auto">
      <h3 className="text-sm font-semibold text-zinc-200 uppercase tracking-wider">Runtime Payload Store</h3>

      {/* RAG Section */}
      {payloads.ragContext && payloads.ragContext.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-purple-400 font-mono">FAISS Vector Search Context ({payloads.ragContext.length} hits)</div>
          <div className="space-y-1.5">
            {payloads.ragContext.map((hit) => (
              <div key={hit.id} className="bg-zinc-950 p-2 rounded border border-zinc-850 text-xs text-zinc-400 font-mono">
                {hit.text}
                <div className="text-[10px] text-zinc-600 mt-1">L2 Proximity Score: {hit.similarity_distance?.toFixed(4)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tools / Pandas Section */}
      {payloads.toolExecution && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-amber-400 font-mono">Pandas Analytics Output</div>
          <pre className="bg-zinc-950 p-3 rounded border border-zinc-850 text-xs font-mono text-zinc-300 overflow-x-auto overflow-y-auto max-h-75">
            {JSON.stringify(payloads.toolExecution, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};