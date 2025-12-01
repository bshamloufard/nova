import { useRef, useEffect, useCallback } from 'react';
import { usePlayerStore } from '../../stores/playerStore';
import type { WordTimestamp } from '../../types';

interface TranscriptViewerProps {
  words: WordTimestamp[];
}

export function TranscriptViewer({ words }: TranscriptViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeWordRef = useRef<HTMLSpanElement>(null);
  const userScrollingRef = useRef(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const { currentTimeMs, setCurrentTimeMs, isPlaying } = usePlayerStore();

  // Handle user scroll - disable auto-scroll temporarily
  const handleScroll = useCallback(() => {
    if (isPlaying) {
      userScrollingRef.current = true;
      
      // Clear existing timeout
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      
      // Re-enable auto-scroll after 3 seconds of no scrolling
      scrollTimeoutRef.current = setTimeout(() => {
        userScrollingRef.current = false;
      }, 3000);
    }
  }, [isPlaying]);

  // Auto-scroll to active word (only if user isn't scrolling)
  useEffect(() => {
    if (userScrollingRef.current) return;
    
    if (activeWordRef.current && containerRef.current) {
      const container = containerRef.current;
      const activeWord = activeWordRef.current;

      const containerRect = container.getBoundingClientRect();
      const wordRect = activeWord.getBoundingClientRect();

      // Check if word is outside visible area
      const isAbove = wordRect.top < containerRect.top + 50;
      const isBelow = wordRect.bottom > containerRect.bottom - 50;

      if (isAbove || isBelow) {
        activeWord.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      }
    }
  }, [currentTimeMs]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  const isWordActive = useCallback(
    (word: WordTimestamp): boolean => {
      return currentTimeMs >= word.start_ms && currentTimeMs < word.end_ms;
    },
    [currentTimeMs]
  );

  const getWordClasses = useCallback(
    (word: WordTimestamp, isActive: boolean): string => {
      const baseClasses =
        'inline-block px-0.5 py-0.5 mx-0.5 rounded transition-all duration-100 cursor-pointer hover:bg-gray-100';

      if (isActive) {
        return `${baseClasses} bg-primary-100 text-primary-900 font-semibold ring-2 ring-primary-400 scale-105`;
      }

      if (word.was_orchestrator_resolved) {
        return `${baseClasses} bg-marker-resolved/40 text-purple-800`;
      }

      if (word.is_uncertain) {
        return `${baseClasses} bg-marker-uncertain/40 text-red-700`;
      }

      return `${baseClasses} text-gray-700`;
    },
    []
  );

  const handleWordClick = useCallback(
    (word: WordTimestamp) => {
      userScrollingRef.current = false; // Reset scroll lock on click
      setCurrentTimeMs(word.start_ms);
    },
    [setCurrentTimeMs]
  );

  // Group words by speaker (if available)
  const groupedWords = words.reduce<{ speaker: string | null; words: WordTimestamp[] }[]>(
    (acc, word) => {
      const lastGroup = acc[acc.length - 1];
      if (lastGroup && lastGroup.speaker === (word.speaker || null)) {
        lastGroup.words.push(word);
      } else {
        acc.push({
          speaker: word.speaker || null,
          words: [word],
        });
      }
      return acc;
    },
    []
  );

  return (
    <div className="card h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between p-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-800">Transcript</h3>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-marker-resolved/60" />
            <span className="text-gray-400">Resolved</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-marker-uncertain/60" />
            <span className="text-gray-400">Low Conf.</span>
          </span>
        </div>
      </div>

      {/* Transcript content - scrollable */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto scrollbar-thin p-4"
      >
        {groupedWords.map((group, groupIndex) => (
          <div key={groupIndex} className="mb-3">
            {/* Speaker label */}
            {group.speaker && (
              <div className="text-[10px] font-medium text-gray-400 uppercase tracking-wider mb-1">
                Speaker {group.speaker}
              </div>
            )}

            {/* Words */}
            <div className="leading-relaxed text-base">
              {group.words.map((word, wordIndex) => {
                const isActive = isWordActive(word);
                const key = `${groupIndex}-${wordIndex}-${word.start_ms}`;

                return (
                  <span
                    key={key}
                    ref={isActive ? activeWordRef : null}
                    className={getWordClasses(word, isActive)}
                    onClick={() => handleWordClick(word)}
                    title={`${(word.confidence * 100).toFixed(0)}% confidence`}
                  >
                    {word.text}
                  </span>
                );
              })}
            </div>
          </div>
        ))}

        {/* Empty state */}
        {words.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            No transcript available
          </div>
        )}
      </div>

      {/* Footer stats */}
      <div className="flex-shrink-0 px-3 py-2 border-t border-gray-100 flex items-center justify-between text-[10px] text-gray-400">
        <span>{words.length} words</span>
        <span>
          {words.filter((w) => w.was_orchestrator_resolved).length} resolved
        </span>
      </div>
    </div>
  );
}
