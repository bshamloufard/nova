"""Timeline data generator for frontend visualization."""

from typing import List, Optional

from models.transcription import TranscriptionResult
from models.segment import OrchestratorDecision
from models.clinical_data import (
    ClinicalExtraction, TimelineMarker, TimelineData, TimelineMarkerType
)


class TimelineGenerator:
    """
    Generates timeline data for frontend visualization.
    
    Creates markers for:
    - Action items (yellow)
    - Numerical values (green)
    - Uncertain segments (coral)
    - Orchestrator resolved segments (purple)
    """
    
    def generate(
        self,
        transcription: TranscriptionResult,
        orchestrator_decisions: List[OrchestratorDecision],
        clinical_data: ClinicalExtraction
    ) -> TimelineData:
        """
        Generate complete timeline data.
        
        Args:
            transcription: Final transcription result
            orchestrator_decisions: List of orchestrator decisions
            clinical_data: Extracted clinical data
            
        Returns:
            TimelineData for frontend rendering
        """
        markers = []
        
        # Add markers for orchestrator decisions (uncertain -> resolved)
        for decision in orchestrator_decisions:
            segment = decision.segment
            
            # Mark as resolved if successfully orchestrated
            markers.append(TimelineMarker(
                start_ms=segment.start_time_ms,
                end_ms=segment.end_time_ms,
                type=TimelineMarkerType.ORCHESTRATOR_RESOLVED,
                label=f"Resolved: {decision.chosen_source}",
                data={
                    "chosen_source": decision.chosen_source,
                    "reasoning": decision.reasoning,
                    "original_confidence": segment.average_confidence,
                    "new_confidence": decision.confidence_boost,
                    "was_synthesized": decision.was_synthesized
                }
            ))
        
        # Add markers for action items
        for item in clinical_data.action_items:
            # Estimate end time (action items typically span ~5 seconds of speech)
            end_ms = item.timestamp_ms + 5000
            
            markers.append(TimelineMarker(
                start_ms=item.timestamp_ms,
                end_ms=end_ms,
                type=TimelineMarkerType.ACTION_ITEM,
                label=f"{item.category.value}: {item.text[:30]}...",
                data={
                    "text": item.text,
                    "category": item.category.value,
                    "priority": item.priority.value,
                    "keywords": item.keywords
                }
            ))
        
        # Add markers for numerical values
        for value in clinical_data.numerical_values:
            # Numerical values are typically short (~2 seconds)
            end_ms = value.timestamp_ms + 2000
            
            markers.append(TimelineMarker(
                start_ms=value.timestamp_ms,
                end_ms=end_ms,
                type=TimelineMarkerType.NUMERICAL_VALUE,
                label=f"{value.label}: {value.value}{value.unit or ''}",
                data={
                    "value": value.value,
                    "unit": value.unit,
                    "category": value.category.value,
                    "label": value.label,
                    "raw_text": value.raw_text
                }
            ))
        
        # Sort markers by start time
        markers.sort(key=lambda m: m.start_ms)
        
        # Generate word timestamps for karaoke sync
        word_timestamps = self._generate_word_timestamps(
            transcription,
            orchestrator_decisions
        )
        
        return TimelineData(
            duration_ms=transcription.duration_ms,
            markers=markers,
            word_timestamps=word_timestamps
        )
    
    def _generate_word_timestamps(
        self,
        transcription: TranscriptionResult,
        decisions: List[OrchestratorDecision]
    ) -> List[dict]:
        """
        Generate word-level timestamps for karaoke-style highlighting.
        
        Includes metadata about whether each word was uncertain or resolved.
        
        Args:
            transcription: The transcription result
            decisions: Orchestrator decisions for context
            
        Returns:
            List of word timestamp objects for frontend
        """
        word_timestamps = []
        
        # Build a set of time ranges that were orchestrated
        orchestrated_ranges = []
        for decision in decisions:
            orchestrated_ranges.append((
                decision.segment.start_time_ms,
                decision.segment.end_time_ms,
                decision
            ))
        
        for word in transcription.words:
            # Check if this word is in an orchestrated segment
            is_orchestrated = False
            orchestrator_source = None
            
            for start, end, decision in orchestrated_ranges:
                if word.start_time_ms >= start and word.end_time_ms <= end:
                    is_orchestrated = True
                    orchestrator_source = decision.chosen_source
                    break
            
            word_data = {
                "text": word.text,
                "start_ms": word.start_time_ms,
                "end_ms": word.end_time_ms,
                "confidence": word.confidence,
                "speaker": word.speaker,
                "is_uncertain": word.confidence < 0.75 and not is_orchestrated,
                "was_orchestrator_resolved": is_orchestrated,
                "orchestrator_source": orchestrator_source
            }
            
            word_timestamps.append(word_data)
        
        return word_timestamps
    
    def get_marker_summary(self, timeline_data: TimelineData) -> dict:
        """
        Get a summary of markers by type.
        
        Args:
            timeline_data: The generated timeline data
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_markers": len(timeline_data.markers),
            "action_items": 0,
            "numerical_values": 0,
            "uncertain_segments": 0,
            "orchestrator_resolved": 0,
            "duration_seconds": timeline_data.duration_ms / 1000
        }
        
        for marker in timeline_data.markers:
            if marker.type == TimelineMarkerType.ACTION_ITEM:
                summary["action_items"] += 1
            elif marker.type == TimelineMarkerType.NUMERICAL_VALUE:
                summary["numerical_values"] += 1
            elif marker.type == TimelineMarkerType.UNCERTAIN:
                summary["uncertain_segments"] += 1
            elif marker.type == TimelineMarkerType.ORCHESTRATOR_RESOLVED:
                summary["orchestrator_resolved"] += 1
        
        return summary

