"""Deepgram transcription service implementation."""

import os
import httpx
from typing import List, Optional

from .base import BaseTranscriptionService
from models.transcription import TranscriptionResult, Word


class DeepgramService(BaseTranscriptionService):
    """
    Deepgram Nova-3 transcription service.
    
    Features:
    - Word-level confidence scores (0.0-1.0)
    - Speaker diarization
    - Medical vocabulary support
    - Lowest Word Error Rate in industry benchmarks
    """
    
    API_URL = "https://api.deepgram.com/v1/listen"
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
    
    @property
    def model_name(self) -> str:
        return "deepgram-nova-3"
    
    async def transcribe(
        self,
        audio_file_path: str,
        language: str = "en",
        enable_speaker_diarization: bool = True,
        vocabulary_boost: Optional[List[str]] = None
    ) -> TranscriptionResult:
        """Transcribe audio using Deepgram Nova-3."""
        
        # Build query parameters
        params = {
            "model": "nova-2",  # Using nova-2 as it's the latest stable
            "language": language,
            "punctuate": "true",
            "diarize": str(enable_speaker_diarization).lower(),
            "utterances": "true",
            "smart_format": "true",
        }
        
        # Add vocabulary boost (keywords) if provided
        if vocabulary_boost:
            params["keywords"] = ",".join(vocabulary_boost)
        
        # Read audio file
        with open(audio_file_path, "rb") as f:
            audio_data = f.read()
        
        # Determine content type
        ext = os.path.splitext(audio_file_path)[1].lower()
        content_types = {
            ".mp3": "audio/mp3",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".ogg": "audio/ogg",
        }
        content_type = content_types.get(ext, "audio/mp3")
        
        # Make API request
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                self.API_URL,
                params=params,
                content=audio_data,
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": content_type,
                }
            )
            response.raise_for_status()
            result = response.json()
        
        # Parse response into our format
        return self._parse_response(result)
    
    async def transcribe_segment(
        self,
        audio_file_path: str,
        start_time_ms: int,
        end_time_ms: int,
        language: str = "en"
    ) -> TranscriptionResult:
        """Transcribe a specific segment of audio."""
        
        # Extract segment to temp file
        segment_path = self._extract_audio_segment(
            audio_file_path,
            start_time_ms,
            end_time_ms
        )
        
        try:
            # Transcribe the segment
            result = await self.transcribe(
                segment_path,
                language=language,
                enable_speaker_diarization=False
            )
            
            # Adjust timestamps to be relative to original audio
            adjusted_words = []
            for word in result.words:
                adjusted_words.append(Word(
                    text=word.text,
                    start_time_ms=word.start_time_ms + start_time_ms,
                    end_time_ms=word.end_time_ms + start_time_ms,
                    confidence=word.confidence,
                    speaker=word.speaker
                ))
            
            result.words = adjusted_words
            return result
            
        finally:
            # Clean up temp file
            if os.path.exists(segment_path):
                os.remove(segment_path)
    
    def _parse_response(self, response: dict) -> TranscriptionResult:
        """Parse Deepgram API response into TranscriptionResult."""
        
        # Extract results
        results = response.get("results", {})
        channels = results.get("channels", [{}])
        
        if not channels:
            return TranscriptionResult(
                full_text="",
                words=[],
                overall_confidence=0.0,
                duration_ms=0,
                language="en",
                model_name=self.model_name,
                raw_response=response
            )
        
        alternatives = channels[0].get("alternatives", [{}])
        if not alternatives:
            return TranscriptionResult(
                full_text="",
                words=[],
                overall_confidence=0.0,
                duration_ms=0,
                language="en",
                model_name=self.model_name,
                raw_response=response
            )
        
        best_alternative = alternatives[0]
        
        # Parse words
        words = []
        for w in best_alternative.get("words", []):
            words.append(Word(
                text=w.get("word", ""),
                start_time_ms=int(w.get("start", 0) * 1000),
                end_time_ms=int(w.get("end", 0) * 1000),
                confidence=w.get("confidence", 0.0),
                speaker=str(w.get("speaker")) if "speaker" in w else None
            ))
        
        # Get full text and confidence
        full_text = best_alternative.get("transcript", "")
        overall_confidence = best_alternative.get("confidence", 0.0)
        
        # Get duration from metadata
        metadata = results.get("metadata", {})
        duration_ms = int(metadata.get("duration", 0) * 1000)
        
        return TranscriptionResult(
            full_text=full_text,
            words=words,
            overall_confidence=overall_confidence,
            duration_ms=duration_ms,
            language=metadata.get("language", "en"),
            model_name=self.model_name,
            raw_response=response
        )

