import { useCallback } from 'react';
import { usePlayerStore } from '../stores/playerStore';

export function useAudioPlayer() {
  const {
    isPlaying,
    currentTimeMs,
    durationMs,
    playbackRate,
    volume,
    audioUrl,
    setIsPlaying,
    setCurrentTimeMs,
    setPlaybackRate,
    setVolume,
    togglePlayPause,
    seekTo,
  } = usePlayerStore();

  const skipForward = useCallback((seconds: number = 10) => {
    seekTo(currentTimeMs + seconds * 1000);
  }, [currentTimeMs, seekTo]);

  const skipBackward = useCallback((seconds: number = 10) => {
    seekTo(Math.max(0, currentTimeMs - seconds * 1000));
  }, [currentTimeMs, seekTo]);

  const seekToWord = useCallback((startMs: number) => {
    seekTo(startMs);
    if (!isPlaying) {
      setIsPlaying(true);
    }
  }, [seekTo, isPlaying, setIsPlaying]);

  const formatTime = useCallback((ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }, []);

  return {
    // State
    isPlaying,
    currentTimeMs,
    durationMs,
    playbackRate,
    volume,
    audioUrl,
    formattedCurrentTime: formatTime(currentTimeMs),
    formattedDuration: formatTime(durationMs),
    progressPercent: durationMs > 0 ? (currentTimeMs / durationMs) * 100 : 0,

    // Actions
    play: () => setIsPlaying(true),
    pause: () => setIsPlaying(false),
    togglePlayPause,
    setPlaybackRate,
    setVolume,
    seekTo,
    seekToWord,
    skipForward,
    skipBackward,
    setCurrentTimeMs,
  };
}

