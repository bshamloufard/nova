"""Transcription models for Nova."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Word(BaseModel):
    """Represents a single transcribed word with metadata."""
    
    text: str = Field(..., description="The transcribed word text")
    start_time_ms: int = Field(..., description="Start time in milliseconds")
    end_time_ms: int = Field(..., description="End time in milliseconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    speaker: Optional[str] = Field(None, description="Speaker identifier if diarization enabled")
    
    @property
    def duration_ms(self) -> int:
        """Duration of the word in milliseconds."""
        return self.end_time_ms - self.start_time_ms
    
    def is_low_confidence(self, threshold: float = 0.75) -> bool:
        """Check if word confidence is below threshold."""
        return self.confidence < threshold


class TranscriptionResult(BaseModel):
    """Complete transcription result from a single model."""
    
    full_text: str = Field(..., description="Complete transcribed text")
    words: List[Word] = Field(default_factory=list, description="Word-level transcription data")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence score")
    duration_ms: int = Field(..., description="Total audio duration in milliseconds")
    language: str = Field(default="en", description="Detected or specified language")
    model_name: str = Field(..., description="Name of the transcription model used")
    raw_response: Optional[Dict[str, Any]] = Field(None, description="Raw API response for debugging")
    
    @property
    def word_count(self) -> int:
        """Total number of words in transcription."""
        return len(self.words)
    
    def get_words_in_range(self, start_ms: int, end_ms: int) -> List[Word]:
        """Get all words within a time range."""
        return [
            word for word in self.words
            if word.start_time_ms >= start_ms and word.end_time_ms <= end_ms
        ]
    
    def get_text_in_range(self, start_ms: int, end_ms: int) -> str:
        """Get concatenated text for a time range."""
        words = self.get_words_in_range(start_ms, end_ms)
        return " ".join(word.text for word in words)
    
    def get_context_before(self, position_ms: int, word_count: int = 50) -> str:
        """Get context words before a given position."""
        words_before = [w for w in self.words if w.end_time_ms <= position_ms]
        context_words = words_before[-word_count:] if len(words_before) > word_count else words_before
        return " ".join(word.text for word in context_words)
    
    def get_context_after(self, position_ms: int, word_count: int = 50) -> str:
        """Get context words after a given position."""
        words_after = [w for w in self.words if w.start_time_ms >= position_ms]
        context_words = words_after[:word_count]
        return " ".join(word.text for word in context_words)

