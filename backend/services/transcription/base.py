"""Base transcription service interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from models.transcription import TranscriptionResult, Word


class BaseTranscriptionService(ABC):
    """
    Abstract base class for all transcription services.
    Ensures consistent interface across Deepgram, AssemblyAI, and Whisper.
    """
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
    
    @abstractmethod
    async def transcribe(
        self,
        audio_file_path: str,
        language: str = "en",
        enable_speaker_diarization: bool = True,
        vocabulary_boost: Optional[List[str]] = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file and return word-level results.
        
        Args:
            audio_file_path: Path to the audio file
            language: ISO language code (default: English)
            enable_speaker_diarization: Whether to identify different speakers
            vocabulary_boost: List of domain-specific terms to boost recognition
            
        Returns:
            TranscriptionResult with word-level timestamps and confidence
        """
        pass
    
    @abstractmethod
    async def transcribe_segment(
        self,
        audio_file_path: str,
        start_time_ms: int,
        end_time_ms: int,
        language: str = "en"
    ) -> TranscriptionResult:
        """
        Transcribe a specific segment of an audio file.
        Used for re-transcription of uncertain segments.
        
        Args:
            audio_file_path: Path to the audio file
            start_time_ms: Start time in milliseconds
            end_time_ms: End time in milliseconds
            language: ISO language code
            
        Returns:
            TranscriptionResult for the segment
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name/identifier of this transcription model."""
        pass
    
    def _extract_audio_segment(
        self,
        audio_file_path: str,
        start_time_ms: int,
        end_time_ms: int
    ) -> str:
        """
        Extract a segment from an audio file.
        Returns path to temporary file containing the segment.
        """
        from pydub import AudioSegment
        import tempfile
        import os
        
        # Load audio file
        audio = AudioSegment.from_file(audio_file_path)
        
        # Add padding (100ms before and after for better context)
        padding_ms = 100
        start = max(0, start_time_ms - padding_ms)
        end = min(len(audio), end_time_ms + padding_ms)
        
        # Extract segment
        segment = audio[start:end]
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )
        segment.export(temp_file.name, format="mp3")
        
        return temp_file.name
    
    def _calculate_overall_confidence(self, words: List[Word]) -> float:
        """Calculate average confidence from word list."""
        if not words:
            return 0.0
        return sum(w.confidence for w in words) / len(words)

