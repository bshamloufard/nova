import type { ClinicalData } from './clinical';
import type { TimelineData } from './timeline';

// Word-level transcription data
export interface Word {
  text: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
  speaker?: string;
  is_uncertain: boolean;
  was_orchestrator_resolved: boolean;
  orchestrator_source?: string;
}

// Full transcription result
export interface TranscriptionResult {
  full_text: string;
  words: Word[];
  overall_confidence: number;
  duration_ms: number;
  language: string;
  model_name: string;
}

// Uncertain segment data
export interface UncertainSegment {
  start_time_ms: number;
  end_time_ms: number;
  original_text: string;
  average_confidence: number;
  context_before: string;
  context_after: string;
}

// Candidate transcription from a model
export interface CandidateTranscription {
  model_name: string;
  text: string;
  confidence: number;
}

// Orchestrator decision
export interface OrchestratorDecision {
  segment: UncertainSegment;
  candidate_transcriptions: Record<string, CandidateTranscription>;
  chosen_source: 'deepgram' | 'assemblyai' | 'whisper' | 'synthesized';
  final_text: string;
  reasoning: string;
  confidence_boost: number;
  was_synthesized: boolean;
  synthesis_justification?: string;
}

// Job status
export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

// Transcription job
export interface TranscriptionJob {
  job_id: string;
  status: JobStatus;
  progress?: number;
  error?: string;
}

// Full transcription response
export interface TranscriptionResponse {
  job_id: string;
  status: JobStatus;
  result?: {
    transcription: TranscriptionResult;
    orchestrator_decisions: OrchestratorDecision[];
    clinical_data: ClinicalData;
    timeline: TimelineData;
  };
}
