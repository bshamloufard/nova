import axios from 'axios';
import type { TranscriptionJob, TranscriptionResponse } from '../types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 300000, // 5 minutes for long transcriptions
});

// API response types
interface UploadResponse {
  job_id: string;
  status: string;
  message: string;
}

interface StatusResponse {
  job_id: string;
  status: string;
  progress?: number;
  error?: string;
}

/**
 * Upload an audio file for transcription
 */
export async function uploadAudio(file: File): Promise<TranscriptionJob> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/transcribe', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return {
    job_id: response.data.job_id,
    status: response.data.status as TranscriptionJob['status'],
  };
}

/**
 * Get the status of a transcription job
 */
export async function getTranscriptionStatus(jobId: string): Promise<TranscriptionJob> {
  const response = await api.get<StatusResponse>(`/transcription/${jobId}/status`);
  
  return {
    job_id: response.data.job_id,
    status: response.data.status as TranscriptionJob['status'],
    progress: response.data.progress,
    error: response.data.error,
  };
}

/**
 * Get the full transcription result
 */
export async function getTranscriptionResult(jobId: string): Promise<TranscriptionResponse> {
  const response = await api.get<TranscriptionResponse>(`/transcription/${jobId}`);
  return response.data;
}

/**
 * Get the audio URL for a job
 */
export function getAudioUrl(jobId: string): string {
  return `/api/audio/${jobId}`;
}

/**
 * Poll for transcription completion
 */
export async function pollForCompletion(
  jobId: string,
  onProgress?: (progress: number) => void,
  pollInterval: number = 2000,
  maxAttempts: number = 300
): Promise<TranscriptionResponse> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await getTranscriptionStatus(jobId);

    if (status.progress !== undefined && onProgress) {
      onProgress(status.progress);
    }

    if (status.status === 'completed') {
      return await getTranscriptionResult(jobId);
    }

    if (status.status === 'failed') {
      throw new Error(status.error || 'Transcription failed');
    }

    await new Promise(resolve => setTimeout(resolve, pollInterval));
    attempts++;
  }

  throw new Error('Transcription timed out');
}

export default api;

