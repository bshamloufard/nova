import { useTranscriptionStore } from '../../stores/transcriptionStore';
import { usePlayerStore } from '../../stores/playerStore';
import { Timeline } from '../timeline/Timeline';
import { TranscriptViewer } from '../transcript/TranscriptViewer';

export function RightPanel() {
  const { transcription, timelineData } = useTranscriptionStore();
  const { audioUrl } = usePlayerStore();

  if (!transcription || !timelineData) {
    return null;
  }

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Timeline & Controls - Fixed height */}
      <div className="flex-shrink-0">
        <Timeline
          audioUrl={audioUrl || ''}
          durationMs={timelineData.duration_ms}
          markers={timelineData.markers}
        />
      </div>

      {/* Transcript - Takes remaining height, scrollable internally */}
      <div className="flex-1 min-h-0">
        <TranscriptViewer words={timelineData.word_timestamps} />
      </div>
    </div>
  );
}
