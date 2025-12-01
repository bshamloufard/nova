"""AssemblyAI transcription service implementation using official SDK."""

import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

import assemblyai as aai

from .base import BaseTranscriptionService
from models.transcription import TranscriptionResult, Word


class AssemblyAIService(BaseTranscriptionService):
    """
    AssemblyAI Universal transcription service using official SDK.
    
    Features:
    - Word-level confidence (0.0-1.0)
    - Entity detection
    - Speaker diarization
    - Robust file handling
    """
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        # Set the API key for the SDK
        aai.settings.api_key = api_key
        self._executor = ThreadPoolExecutor(max_workers=3)
    
    @property
    def model_name(self) -> str:
        return "assemblyai-universal"
    
    async def transcribe(
        self,
        audio_file_path: str,
        language: str = "en",
        enable_speaker_diarization: bool = True,
        vocabulary_boost: Optional[List[str]] = None
    ) -> TranscriptionResult:
        """Transcribe audio using AssemblyAI SDK."""
        
        # Run synchronous SDK in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self._executor,
            self._transcribe_sync,
            audio_file_path,
            language,
            enable_speaker_diarization,
            vocabulary_boost
        )
        return result
    
    def _transcribe_sync(
        self,
        audio_file_path: str,
        language: str,
        enable_speaker_diarization: bool,
        vocabulary_boost: Optional[List[str]]
    ) -> TranscriptionResult:
        """Synchronous transcription using SDK."""
        
        # Build config
        config = aai.TranscriptionConfig(
            language_code=language,
            speaker_labels=enable_speaker_diarization,
            punctuate=True,
            format_text=True,
        )
        
        # Add word boost if provided
        if vocabulary_boost:
            config.word_boost = vocabulary_boost
            config.boost_param = aai.WordBoost.high
        
        # Create transcriber and transcribe
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_file_path)
        
        # Check for errors
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI transcription failed: {transcript.error}")
        
        return self._parse_transcript(transcript)
    
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
    
    def _parse_transcript(self, transcript: aai.Transcript) -> TranscriptionResult:
        """Parse AssemblyAI transcript into TranscriptionResult."""
        
        # Parse words
        words = []
        if transcript.words:
            for w in transcript.words:
                words.append(Word(
                    text=w.text,
                    start_time_ms=w.start,
                    end_time_ms=w.end,
                    confidence=w.confidence,
                    speaker=str(w.speaker) if hasattr(w, 'speaker') and w.speaker else None
                ))
        
        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(words)
        
        # Get duration
        duration_ms = 0
        if words:
            duration_ms = words[-1].end_time_ms
        elif hasattr(transcript, 'audio_duration') and transcript.audio_duration:
            duration_ms = int(transcript.audio_duration * 1000)
        
        return TranscriptionResult(
            full_text=transcript.text or "",
            words=words,
            overall_confidence=overall_confidence,
            duration_ms=duration_ms,
            language=transcript.language_code or "en",
            model_name=self.model_name,
            raw_response={"id": transcript.id, "status": str(transcript.status)}
        )
