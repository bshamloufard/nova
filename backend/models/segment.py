"""Segment models for uncertain audio and orchestrator decisions."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from .transcription import Word, TranscriptionResult


class UncertainSegment(BaseModel):
    """Represents a segment of audio with low transcription confidence."""
    
    start_time_ms: int = Field(..., description="Segment start time in milliseconds")
    end_time_ms: int = Field(..., description="Segment end time in milliseconds")
    original_words: List[Word] = Field(default_factory=list, description="Original low-confidence words")
    average_confidence: float = Field(..., ge=0.0, le=1.0, description="Average confidence of segment")
    context_before: str = Field(default="", description="Text context before the segment")
    context_after: str = Field(default="", description="Text context after the segment")
    
    @property
    def duration_ms(self) -> int:
        """Duration of the segment in milliseconds."""
        return self.end_time_ms - self.start_time_ms
    
    @property
    def original_text(self) -> str:
        """Get the original transcribed text for this segment."""
        return " ".join(word.text for word in self.original_words)


class CandidateTranscription(BaseModel):
    """A transcription candidate from one model for an uncertain segment."""
    
    model_name: str = Field(..., description="Name of the model that produced this")
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model's confidence score")
    words: List[Word] = Field(default_factory=list, description="Word-level data if available")


class OrchestratorDecision(BaseModel):
    """
    Decision made by the orchestrator for an uncertain segment.
    
    Contains all candidate transcriptions and the final chosen result.
    """
    
    segment: UncertainSegment = Field(..., description="The uncertain segment being resolved")
    candidate_transcriptions: Dict[str, CandidateTranscription] = Field(
        default_factory=dict,
        description="Transcriptions from each model (keyed by model name)"
    )
    chosen_source: str = Field(
        ...,
        description="Which model was chosen: 'deepgram', 'assemblyai', 'whisper', or 'synthesized'"
    )
    final_text: str = Field(..., description="The final selected or synthesized text")
    reasoning: str = Field(..., description="LLM's explanation for the decision")
    confidence_boost: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="New confidence level after orchestration"
    )
    was_synthesized: bool = Field(
        default=False,
        description="Whether the LLM synthesized its own transcription"
    )
    synthesis_justification: Optional[str] = Field(
        None,
        description="If synthesized, why all candidates were rejected"
    )
    
    @property
    def all_candidates_text(self) -> Dict[str, str]:
        """Get just the text from each candidate."""
        return {
            name: candidate.text
            for name, candidate in self.candidate_transcriptions.items()
        }

