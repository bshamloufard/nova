import { useState } from 'react';
import { usePlayerStore } from '../../stores/playerStore';
import type { OrchestratorDecision } from '../../types';

interface OrchestratorDecisionsProps {
  decisions: OrchestratorDecision[];
}

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

const SOURCE_LABELS: Record<string, { label: string; color: string }> = {
  deepgram: { label: 'Deepgram', color: 'bg-blue-100 text-blue-700' },
  assemblyai: { label: 'AssemblyAI', color: 'bg-green-100 text-green-700' },
  whisper: { label: 'Whisper', color: 'bg-orange-100 text-orange-700' },
  synthesized: { label: 'Synthesized', color: 'bg-purple-100 text-purple-700' },
};

export function OrchestratorDecisions({ decisions }: OrchestratorDecisionsProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const { setCurrentTimeMs } = usePlayerStore();

  if (decisions.length === 0) {
    return null;
  }

  return (
    <div className="card p-3">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
        <span>⚙️</span>
        Orchestrator
        <span className="ml-auto bg-marker-resolved/50 text-purple-700 px-1.5 py-0.5 rounded-full text-[10px]">
          {decisions.length}
        </span>
      </h3>

      <div className="space-y-1.5 max-h-48 overflow-y-auto scrollbar-thin pr-1">
        {decisions.map((decision, index) => {
          const isExpanded = expandedIndex === index;
          const sourceInfo = SOURCE_LABELS[decision.chosen_source] || {
            label: decision.chosen_source,
            color: 'bg-gray-100 text-gray-700',
          };

          return (
            <div
              key={index}
              className="bg-gray-50 rounded-lg overflow-hidden"
            >
              {/* Header */}
              <div
                onClick={() => setExpandedIndex(isExpanded ? null : index)}
                className="p-2 cursor-pointer hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <svg
                      className={`w-3 h-3 text-gray-400 transition-transform ${
                        isExpanded ? 'rotate-90' : ''
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                    <span className="text-[10px] font-medium text-gray-600">
                      {formatTime(decision.segment.start_time_ms)} -{' '}
                      {formatTime(decision.segment.end_time_ms)}
                    </span>
                  </div>
                  <span className={`px-1.5 py-0.5 text-[10px] rounded ${sourceInfo.color}`}>
                    {sourceInfo.label}
                  </span>
                </div>

                <p className="mt-1 text-[10px] text-gray-500 line-clamp-1 pl-4">
                  "{decision.final_text}"
                </p>
              </div>

              {/* Expanded content */}
              {isExpanded && (
                <div className="px-2 pb-2 space-y-2 border-t border-gray-200 pt-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setCurrentTimeMs(decision.segment.start_time_ms);
                    }}
                    className="text-[10px] text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                    Jump to timestamp
                  </button>

                  {/* Candidates */}
                  <div className="space-y-1">
                    <p className="text-[10px] font-medium text-gray-400 uppercase">
                      Candidates
                    </p>
                    {Object.entries(decision.candidate_transcriptions).map(
                      ([source, candidate]) => {
                        const isChosen = source === decision.chosen_source;
                        return (
                          <div
                            key={source}
                            className={`p-1.5 rounded text-[10px] ${
                              isChosen
                                ? 'bg-primary-50 border border-primary-200'
                                : 'bg-white border border-gray-100'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-0.5">
                              <span className={isChosen ? 'text-primary-700 font-medium' : 'text-gray-500'}>
                                {SOURCE_LABELS[source]?.label || source}
                                {isChosen && ' ✓'}
                              </span>
                              <span className="text-gray-400">
                                {(candidate.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-gray-600 line-clamp-2">
                              "{candidate.text}"
                            </p>
                          </div>
                        );
                      }
                    )}
                  </div>

                  {/* Reasoning */}
                  <div>
                    <p className="text-[10px] font-medium text-gray-400 uppercase mb-0.5">
                      Reasoning
                    </p>
                    <p className="text-[10px] text-gray-600 bg-white p-1.5 rounded border border-gray-100">
                      {decision.reasoning}
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
