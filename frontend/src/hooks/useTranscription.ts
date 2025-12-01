import { useCallback } from 'react';
import { useTranscriptionStore } from '../stores/transcriptionStore';
import { usePlayerStore } from '../stores/playerStore';
import { uploadAudio, pollForCompletion, getAudioUrl } from '../services/api';

export function useTranscription() {
  const {
    jobId,
    status,
    progress,
    error,
    transcription,
    orchestratorDecisions,
    clinicalData,
    timelineData,
    setJobId,
    setStatus,
    setProgress,
    setError,
    setResult,
    reset,
  } = useTranscriptionStore();

  const { setAudioUrl, setDurationMs, reset: resetPlayer } = usePlayerStore();

  const startTranscription = useCallback(async (file: File) => {
    try {
      // Reset state
      reset();
      resetPlayer();

      // Start upload
      setStatus('pending');
      setProgress(0);

      const job = await uploadAudio(file);
      setJobId(job.job_id);
      setStatus('processing');

      // Set audio URL for playback
      setAudioUrl(getAudioUrl(job.job_id));

      // Poll for completion
      const result = await pollForCompletion(job.job_id, (prog) => {
        setProgress(prog);
      });

      // Set the result
      if (result.result) {
        setResult(result.result);
        setDurationMs(result.result.timeline.duration_ms);
      }

      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      setStatus('failed');
      throw err;
    }
  }, [reset, resetPlayer, setStatus, setProgress, setJobId, setAudioUrl, setResult, setDurationMs, setError]);

  const resetAll = useCallback(() => {
    reset();
    resetPlayer();
  }, [reset, resetPlayer]);

  return {
    // State
    jobId,
    status,
    progress,
    error,
    transcription,
    orchestratorDecisions,
    clinicalData,
    timelineData,
    isLoading: status === 'pending' || status === 'processing',
    isComplete: status === 'completed',
    isFailed: status === 'failed',

    // Actions
    startTranscription,
    reset: resetAll,
  };
}

