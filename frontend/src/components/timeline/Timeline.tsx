import { useEffect, useRef, useCallback } from 'react';
import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js';
import { usePlayerStore } from '../../stores/playerStore';
import type { TimelineMarker } from '../../types';
import { MARKER_COLORS, MARKER_LABELS } from '../../types';

interface TimelineProps {
  audioUrl: string;
  durationMs: number;
  markers: TimelineMarker[];
}

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export function Timeline({ audioUrl, durationMs, markers }: TimelineProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<RegionsPlugin | null>(null);
  const isSeekingRef = useRef(false);

  const {
    isPlaying,
    currentTimeMs,
    playbackRate,
    volume,
    setIsPlaying,
    setCurrentTimeMs,
    setDurationMs,
    setPlaybackRate,
    setVolume,
  } = usePlayerStore();

  // Initialize WaveSurfer
  useEffect(() => {
    if (!waveformRef.current || !audioUrl) return;

    // Create regions plugin
    const regions = RegionsPlugin.create();
    regionsRef.current = regions;

    // Create WaveSurfer instance
    const ws = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#C7D2FE',
      progressColor: '#6366F1',
      cursorColor: '#4F46E5',
      cursorWidth: 2,
      height: 60,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      plugins: [regions],
    });

    wavesurferRef.current = ws;

    // Load audio
    ws.load(audioUrl);

    // Event handlers
    ws.on('ready', () => {
      setDurationMs(ws.getDuration() * 1000);

      // Add marker regions
      markers.forEach((marker, index) => {
        regions.addRegion({
          start: marker.start_ms / 1000,
          end: marker.end_ms / 1000,
          color: MARKER_COLORS[marker.type],
          drag: false,
          resize: false,
          id: `marker-${index}`,
        });
      });
    });

    ws.on('audioprocess', () => {
      if (!isSeekingRef.current) {
        setCurrentTimeMs(ws.getCurrentTime() * 1000);
      }
    });

    ws.on('seeking', () => {
      setCurrentTimeMs(ws.getCurrentTime() * 1000);
    });

    ws.on('play', () => setIsPlaying(true));
    ws.on('pause', () => setIsPlaying(false));
    ws.on('finish', () => setIsPlaying(false));

    return () => {
      ws.destroy();
    };
  }, [audioUrl]);

  // Update markers when they change
  useEffect(() => {
    const regions = regionsRef.current;
    if (!regions) return;

    regions.clearRegions();

    markers.forEach((marker, index) => {
      regions.addRegion({
        start: marker.start_ms / 1000,
        end: marker.end_ms / 1000,
        color: MARKER_COLORS[marker.type],
        drag: false,
        resize: false,
        id: `marker-${index}`,
      });
    });
  }, [markers]);

  // Sync playback state
  useEffect(() => {
    const ws = wavesurferRef.current;
    if (!ws) return;

    if (isPlaying && !ws.isPlaying()) {
      ws.play();
    } else if (!isPlaying && ws.isPlaying()) {
      ws.pause();
    }
  }, [isPlaying]);

  // Sync playback rate
  useEffect(() => {
    const ws = wavesurferRef.current;
    if (ws) {
      ws.setPlaybackRate(playbackRate);
    }
  }, [playbackRate]);

  // Sync volume
  useEffect(() => {
    const ws = wavesurferRef.current;
    if (ws) {
      ws.setVolume(volume);
    }
  }, [volume]);

  // CRITICAL: Seek wavesurfer when currentTimeMs changes from external source (clicking action items, etc.)
  useEffect(() => {
    const ws = wavesurferRef.current;
    if (!ws || !ws.getDuration()) return;

    const wsCurrentTime = ws.getCurrentTime() * 1000;
    const timeDiff = Math.abs(wsCurrentTime - currentTimeMs);

    // Only seek if the difference is significant (more than 500ms)
    // This prevents feedback loops from the audioprocess event
    if (timeDiff > 500) {
      isSeekingRef.current = true;
      const seekPosition = currentTimeMs / (ws.getDuration() * 1000);
      ws.seekTo(Math.min(Math.max(seekPosition, 0), 1));
      
      // Reset seeking flag after a short delay
      setTimeout(() => {
        isSeekingRef.current = false;
      }, 100);
    }
  }, [currentTimeMs]);

  const handlePlayPause = useCallback(() => {
    const ws = wavesurferRef.current;
    if (ws) {
      ws.playPause();
    }
  }, []);

  const skipForward = useCallback(() => {
    const ws = wavesurferRef.current;
    if (ws) {
      const newTime = Math.min(ws.getCurrentTime() + 10, ws.getDuration());
      ws.seekTo(newTime / ws.getDuration());
    }
  }, []);

  const skipBackward = useCallback(() => {
    const ws = wavesurferRef.current;
    if (ws) {
      const newTime = Math.max(ws.getCurrentTime() - 10, 0);
      ws.seekTo(newTime / ws.getDuration());
    }
  }, []);

  const playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2];

  return (
    <div className="card p-4">
      {/* Waveform with integrated controls */}
      <div className="flex items-center gap-3 mb-3">
        {/* Play/Pause Button */}
        <button
          onClick={handlePlayPause}
          className="w-10 h-10 flex-shrink-0 rounded-full bg-primary-500 hover:bg-primary-600 transition-colors flex items-center justify-center shadow-md"
        >
          {isPlaying ? (
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        {/* Skip backward */}
        <button
          onClick={skipBackward}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          title="Skip back 10s"
        >
          <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0019 16V8a1 1 0 00-1.6-.8l-5.333 4zM4.066 11.2a1 1 0 000 1.6l5.334 4A1 1 0 0011 16V8a1 1 0 00-1.6-.8l-5.334 4z" />
          </svg>
        </button>

        {/* Waveform */}
        <div className="flex-1 min-w-0">
          <div
            ref={waveformRef}
            className="w-full rounded-lg overflow-hidden bg-gray-50 cursor-pointer"
          />
        </div>

        {/* Skip forward */}
        <button
          onClick={skipForward}
          className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          title="Skip forward 10s"
        >
          <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.933 12.8a1 1 0 000-1.6L6.6 7.2A1 1 0 005 8v8a1 1 0 001.6.8l5.333-4zM19.933 12.8a1 1 0 000-1.6l-5.333-4A1 1 0 0013 8v8a1 1 0 001.6.8l5.333-4z" />
          </svg>
        </button>

        {/* Time display */}
        <div className="text-xs font-mono text-gray-500 w-20 text-right flex-shrink-0">
          {formatTime(currentTimeMs)} / {formatTime(durationMs)}
        </div>
      </div>

      {/* Bottom row: Legend and controls */}
      <div className="flex items-center justify-between">
        {/* Timeline Legend */}
        <div className="flex flex-wrap gap-3 text-xs">
          {Object.entries(MARKER_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: color }}
              />
              <span className="text-gray-500">
                {MARKER_LABELS[type as keyof typeof MARKER_LABELS]}
              </span>
            </div>
          ))}
        </div>

        {/* Speed and volume controls */}
        <div className="flex items-center gap-3">
          {/* Volume */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setVolume(volume === 0 ? 1 : 0)}
              className="p-1 rounded hover:bg-gray-100"
            >
              {volume === 0 ? (
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                </svg>
              )}
            </button>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={volume}
              onChange={(e) => setVolume(Number(e.target.value))}
              className="w-14 h-1 bg-gray-200 rounded-lg appearance-none cursor-pointer
                         [&::-webkit-slider-thumb]:appearance-none
                         [&::-webkit-slider-thumb]:w-2.5
                         [&::-webkit-slider-thumb]:h-2.5
                         [&::-webkit-slider-thumb]:bg-gray-400
                         [&::-webkit-slider-thumb]:rounded-full"
            />
          </div>

          {/* Speed selector */}
          <div className="flex items-center gap-0.5">
            {playbackRates.map((rate) => (
              <button
                key={rate}
                onClick={() => setPlaybackRate(rate)}
                className={`
                  px-1.5 py-0.5 text-[10px] font-medium rounded transition-colors
                  ${
                    playbackRate === rate
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-400 hover:bg-gray-100'
                  }
                `}
              >
                {rate}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
