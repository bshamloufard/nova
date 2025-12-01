import { create } from 'zustand';
import type {
  TranscriptionResult,
  OrchestratorDecision,
  ClinicalData,
  TimelineData,
  JobStatus,
} from '../types';

interface TranscriptionState {
  // Job state
  jobId: string | null;
  status: JobStatus | null;
  progress: number;
  error: string | null;

  // Result data
  transcription: TranscriptionResult | null;
  orchestratorDecisions: OrchestratorDecision[];
  clinicalData: ClinicalData | null;
  timelineData: TimelineData | null;

  // Actions
  setJobId: (jobId: string) => void;
  setStatus: (status: JobStatus) => void;
  setProgress: (progress: number) => void;
  setError: (error: string | null) => void;
  setResult: (result: {
    transcription: TranscriptionResult;
    orchestrator_decisions: OrchestratorDecision[];
    clinical_data: ClinicalData;
    timeline: TimelineData;
  }) => void;
  reset: () => void;
}

const initialState = {
  jobId: null,
  status: null,
  progress: 0,
  error: null,
  transcription: null,
  orchestratorDecisions: [],
  clinicalData: null,
  timelineData: null,
};

export const useTranscriptionStore = create<TranscriptionState>((set) => ({
  ...initialState,

  setJobId: (jobId) => set({ jobId }),
  
  setStatus: (status) => set({ status }),
  
  setProgress: (progress) => set({ progress }),
  
  setError: (error) => set({ error, status: error ? 'failed' : null }),
  
  setResult: (result) => set({
    transcription: result.transcription,
    orchestratorDecisions: result.orchestrator_decisions,
    clinicalData: result.clinical_data,
    timelineData: result.timeline,
    status: 'completed',
    progress: 1,
  }),
  
  reset: () => set(initialState),
}));

