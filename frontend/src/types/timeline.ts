// Timeline marker types
export type TimelineMarkerType = 'action_item' | 'numerical_value' | 'uncertain' | 'orchestrator_resolved';

// Timeline marker
export interface TimelineMarker {
  start_ms: number;
  end_ms: number;
  type: TimelineMarkerType;
  label?: string;
  data?: Record<string, unknown>;
}

// Word timestamp for karaoke sync
export interface WordTimestamp {
  text: string;
  start_ms: number;
  end_ms: number;
  confidence: number;
  speaker?: string;
  is_uncertain: boolean;
  was_orchestrator_resolved: boolean;
  orchestrator_source?: string;
}

// Complete timeline data
export interface TimelineData {
  duration_ms: number;
  markers: TimelineMarker[];
  word_timestamps: WordTimestamp[];
}

// Marker type display info
export const MARKER_COLORS: Record<TimelineMarkerType, string> = {
  action_item: 'rgba(253, 230, 138, 0.6)',      // Soft yellow
  numerical_value: 'rgba(187, 247, 208, 0.6)',  // Soft green
  uncertain: 'rgba(254, 202, 202, 0.6)',        // Soft coral
  orchestrator_resolved: 'rgba(221, 214, 254, 0.6)', // Soft purple
};

export const MARKER_LABELS: Record<TimelineMarkerType, string> = {
  action_item: 'Action Item',
  numerical_value: 'Numerical Value',
  uncertain: 'Uncertain',
  orchestrator_resolved: 'Orchestrator Resolved',
};

