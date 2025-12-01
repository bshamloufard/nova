"""Confidence analyzer for identifying uncertain transcription segments."""

from typing import List

from models.transcription import TranscriptionResult, Word
from models.segment import UncertainSegment


class ConfidenceAnalyzer:
    """
    Analyzes transcription results to identify segments with low confidence.
    
    Groups consecutive low-confidence words into segments for orchestration.
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.75,
        min_segment_duration_ms: int = 500,
        max_segment_duration_ms: int = 10000,
        context_window_words: int = 50
    ):
        """
        Initialize the confidence analyzer.
        
        Args:
            confidence_threshold: Words below this confidence trigger orchestration
            min_segment_duration_ms: Minimum segment length to consider
            max_segment_duration_ms: Maximum segment length for re-transcription
            context_window_words: Number of context words before/after segment
        """
        self.confidence_threshold = confidence_threshold
        self.min_segment_duration_ms = min_segment_duration_ms
        self.max_segment_duration_ms = max_segment_duration_ms
        self.context_window_words = context_window_words
    
    def identify_uncertain_segments(
        self,
        transcription: TranscriptionResult
    ) -> List[UncertainSegment]:
        """
        Scan transcription for words below confidence threshold.
        Group consecutive low-confidence words into segments.
        
        Args:
            transcription: The transcription result to analyze
            
        Returns:
            List of UncertainSegment objects
        """
        segments = []
        current_segment_words: List[Word] = []
        
        for i, word in enumerate(transcription.words):
            if word.confidence < self.confidence_threshold:
                # Add to current segment
                current_segment_words.append(word)
            else:
                # End current segment if any
                if current_segment_words:
                    segment = self._create_segment(
                        current_segment_words,
                        transcription,
                        i
                    )
                    if segment:
                        segments.append(segment)
                    current_segment_words = []
        
        # Handle segment at end of transcription
        if current_segment_words:
            segment = self._create_segment(
                current_segment_words,
                transcription,
                len(transcription.words)
            )
            if segment:
                segments.append(segment)
        
        # Merge overlapping or adjacent segments
        segments = self._merge_adjacent_segments(segments)
        
        # Split segments that are too long
        segments = self._split_long_segments(segments)
        
        return segments
    
    def _create_segment(
        self,
        words: List[Word],
        transcription: TranscriptionResult,
        current_index: int
    ) -> UncertainSegment | None:
        """
        Create an UncertainSegment from a list of low-confidence words.
        
        Args:
            words: The low-confidence words in this segment
            transcription: Full transcription for context
            current_index: Current position in word list
            
        Returns:
            UncertainSegment or None if segment is too short
        """
        if not words:
            return None
        
        # Calculate segment boundaries
        start_time_ms = words[0].start_time_ms
        end_time_ms = words[-1].end_time_ms
        
        # Check minimum duration
        duration_ms = end_time_ms - start_time_ms
        if duration_ms < self.min_segment_duration_ms:
            return None
        
        # Calculate average confidence
        avg_confidence = sum(w.confidence for w in words) / len(words)
        
        # Get context before and after
        context_before = transcription.get_context_before(
            start_time_ms,
            self.context_window_words
        )
        context_after = transcription.get_context_after(
            end_time_ms,
            self.context_window_words
        )
        
        return UncertainSegment(
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            original_words=words,
            average_confidence=avg_confidence,
            context_before=context_before,
            context_after=context_after
        )
    
    def _merge_adjacent_segments(
        self,
        segments: List[UncertainSegment],
        gap_threshold_ms: int = 1000
    ) -> List[UncertainSegment]:
        """
        Merge segments that are close together.
        
        Args:
            segments: List of segments to potentially merge
            gap_threshold_ms: Maximum gap between segments to merge
            
        Returns:
            Merged list of segments
        """
        if not segments:
            return []
        
        merged = [segments[0]]
        
        for segment in segments[1:]:
            last = merged[-1]
            gap = segment.start_time_ms - last.end_time_ms
            
            if gap <= gap_threshold_ms:
                # Merge segments
                merged_words = last.original_words + segment.original_words
                merged_confidence = (
                    (last.average_confidence * len(last.original_words) +
                     segment.average_confidence * len(segment.original_words)) /
                    len(merged_words)
                )
                
                merged[-1] = UncertainSegment(
                    start_time_ms=last.start_time_ms,
                    end_time_ms=segment.end_time_ms,
                    original_words=merged_words,
                    average_confidence=merged_confidence,
                    context_before=last.context_before,
                    context_after=segment.context_after
                )
            else:
                merged.append(segment)
        
        return merged
    
    def _split_long_segments(
        self,
        segments: List[UncertainSegment]
    ) -> List[UncertainSegment]:
        """
        Split segments that exceed maximum duration.
        
        Args:
            segments: List of segments to potentially split
            
        Returns:
            List with long segments split
        """
        result = []
        
        for segment in segments:
            duration = segment.end_time_ms - segment.start_time_ms
            
            if duration <= self.max_segment_duration_ms:
                result.append(segment)
            else:
                # Split into chunks
                words = segment.original_words
                chunk_words: List[Word] = []
                chunk_start_ms = words[0].start_time_ms if words else 0
                
                for word in words:
                    chunk_words.append(word)
                    chunk_duration = word.end_time_ms - chunk_start_ms
                    
                    if chunk_duration >= self.max_segment_duration_ms:
                        # Create segment from chunk
                        avg_conf = sum(w.confidence for w in chunk_words) / len(chunk_words)
                        result.append(UncertainSegment(
                            start_time_ms=chunk_start_ms,
                            end_time_ms=word.end_time_ms,
                            original_words=chunk_words.copy(),
                            average_confidence=avg_conf,
                            context_before=segment.context_before,
                            context_after=segment.context_after
                        ))
                        chunk_words = []
                        chunk_start_ms = word.end_time_ms
                
                # Add remaining words
                if chunk_words:
                    avg_conf = sum(w.confidence for w in chunk_words) / len(chunk_words)
                    result.append(UncertainSegment(
                        start_time_ms=chunk_start_ms,
                        end_time_ms=chunk_words[-1].end_time_ms,
                        original_words=chunk_words,
                        average_confidence=avg_conf,
                        context_before=segment.context_before,
                        context_after=segment.context_after
                    ))
        
        return result
    
    def get_statistics(
        self,
        transcription: TranscriptionResult
    ) -> dict:
        """
        Get statistics about confidence distribution.
        
        Args:
            transcription: Transcription to analyze
            
        Returns:
            Dictionary with confidence statistics
        """
        if not transcription.words:
            return {
                "total_words": 0,
                "low_confidence_words": 0,
                "low_confidence_percentage": 0.0,
                "average_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0
            }
        
        confidences = [w.confidence for w in transcription.words]
        low_conf_count = sum(1 for c in confidences if c < self.confidence_threshold)
        
        return {
            "total_words": len(confidences),
            "low_confidence_words": low_conf_count,
            "low_confidence_percentage": (low_conf_count / len(confidences)) * 100,
            "average_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "confidence_threshold": self.confidence_threshold
        }

