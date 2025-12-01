import { create } from 'zustand';

interface PlayerState {
  // Playback state
  isPlaying: boolean;
  currentTimeMs: number;
  durationMs: number;
  playbackRate: number;
  volume: number;

  // Audio URL
  audioUrl: string | null;

  // Actions
  setIsPlaying: (isPlaying: boolean) => void;
  setCurrentTimeMs: (timeMs: number) => void;
  setDurationMs: (durationMs: number) => void;
  setPlaybackRate: (rate: number) => void;
  setVolume: (volume: number) => void;
  setAudioUrl: (url: string | null) => void;
  togglePlayPause: () => void;
  seekTo: (timeMs: number) => void;
  reset: () => void;
}

const initialState = {
  isPlaying: false,
  currentTimeMs: 0,
  durationMs: 0,
  playbackRate: 1,
  volume: 1,
  audioUrl: null,
};

export const usePlayerStore = create<PlayerState>((set, get) => ({
  ...initialState,

  setIsPlaying: (isPlaying) => set({ isPlaying }),
  
  setCurrentTimeMs: (timeMs) => set({ currentTimeMs: timeMs }),
  
  setDurationMs: (durationMs) => set({ durationMs }),
  
  setPlaybackRate: (rate) => set({ playbackRate: rate }),
  
  setVolume: (volume) => set({ volume }),
  
  setAudioUrl: (url) => set({ audioUrl: url }),
  
  togglePlayPause: () => set((state) => ({ isPlaying: !state.isPlaying })),
  
  seekTo: (timeMs) => {
    const { durationMs } = get();
    const clampedTime = Math.max(0, Math.min(timeMs, durationMs));
    set({ currentTimeMs: clampedTime });
  },
  
  reset: () => set(initialState),
}));

