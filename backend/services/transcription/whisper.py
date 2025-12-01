"""OpenAI Whisper transcription service implementation."""

import os
import math
from typing import List, Optional
from openai import AsyncOpenAI

from .base import BaseTranscriptionService
from models.transcription import TranscriptionResult, Word


class WhisperService(BaseTranscriptionService):
    """
    OpenAI Whisper transcription service.
    
    Features:
    - 99+ language support
    - Robust to background noise
    - Word-level timestamps via verbose_json
    - avg_logprob for segment confidence
    """
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = AsyncOpenAI(api_key=api_key)
    
    @property
    def model_name(self) -> str:
        return "whisper-1"
    
    async def transcribe(
        self,
        audio_file_path: str,
        language: str = "en",
        enable_speaker_diarization: bool = True,
        vocabulary_boost: Optional[List[str]] = None
    ) -> TranscriptionResult:
        """Transcribe audio using OpenAI Whisper."""
        
        # Build prompt with vocabulary boost
        prompt = ""
        if vocabulary_boost:
            # Whisper uses prompts for context/vocabulary
            prompt = f"Medical terms: {', '.join(vocabulary_boost)}. "
        
        # Open audio file and transcribe
        with open(audio_file_path, "rb") as audio_file:
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language if language != "auto" else None,
                response_format="verbose_json",
                timestamp_granularities=["word", "segment"],
                prompt=prompt if prompt else None
            )
        
        return self._parse_response(response)
    
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
    
    def _parse_response(self, response) -> TranscriptionResult:
        """Parse Whisper API response into TranscriptionResult."""
        
        # Response is a Transcription object, convert to dict for processing
        response_dict = response.model_dump() if hasattr(response, 'model_dump') else dict(response)
        
        words = []
        overall_confidence = 0.8  # Default confidence for Whisper
        
        # Parse word-level timestamps if available
        if "words" in response_dict and response_dict["words"]:
            for w in response_dict["words"]:
                # Whisper doesn't provide word-level confidence
                # We'll use segment-level avg_logprob to estimate
                words.append(Word(
                    text=w.get("word", "").strip(),
                    start_time_ms=int(w.get("start", 0) * 1000),
                    end_time_ms=int(w.get("end", 0) * 1000),
                    confidence=0.85,  # Default confidence
                    speaker=None
                ))
        
        # Calculate confidence from segments if available
        if "segments" in response_dict and response_dict["segments"]:
            segments = response_dict["segments"]
            
            # If no word-level data, create words from segments
            if not words:
                for seg in segments:
                    # Create words by splitting segment text
                    seg_text = seg.get("text", "").strip()
                    seg_start = seg.get("start", 0)
                    seg_end = seg.get("end", 0)
                    
                    # Simple word splitting with estimated timestamps
                    seg_words = seg_text.split()
                    if seg_words:
                        word_duration = (seg_end - seg_start) / len(seg_words)
                        for i, word_text in enumerate(seg_words):
                            word_start = seg_start + (i * word_duration)
                            word_end = word_start + word_duration
                            
                            # Convert avg_logprob to confidence (sigmoid-like)
                            avg_logprob = seg.get("avg_logprob", -0.5)
                            confidence = self._logprob_to_confidence(avg_logprob)
                            
                            words.append(Word(
                                text=word_text,
                                start_time_ms=int(word_start * 1000),
                                end_time_ms=int(word_end * 1000),
                                confidence=confidence,
                                speaker=None
                            ))
            else:
                # Update word confidences from segment data
                for seg in segments:
                    avg_logprob = seg.get("avg_logprob", -0.5)
                    seg_start_ms = int(seg.get("start", 0) * 1000)
                    seg_end_ms = int(seg.get("end", 0) * 1000)
                    confidence = self._logprob_to_confidence(avg_logprob)
                    
                    # Update confidence for words in this segment
                    for word in words:
                        if word.start_time_ms >= seg_start_ms and word.end_time_ms <= seg_end_ms:
                            word.confidence = confidence
            
            # Calculate overall confidence from segment avg_logprobs
            avg_logprobs = [s.get("avg_logprob", -0.5) for s in segments]
            if avg_logprobs:
                avg_logprob = sum(avg_logprobs) / len(avg_logprobs)
                overall_confidence = self._logprob_to_confidence(avg_logprob)
        
        # Calculate overall confidence from words
        if words:
            overall_confidence = self._calculate_overall_confidence(words)
        
        # Get duration from last word end time or response duration
        duration_ms = 0
        if words:
            duration_ms = words[-1].end_time_ms
        elif "duration" in response_dict:
            duration_ms = int(response_dict["duration"] * 1000)
        
        return TranscriptionResult(
            full_text=response_dict.get("text", "").strip(),
            words=words,
            overall_confidence=overall_confidence,
            duration_ms=duration_ms,
            language=response_dict.get("language", "en"),
            model_name=self.model_name,
            raw_response=response_dict
        )
    
    def _logprob_to_confidence(self, avg_logprob: float) -> float:
        """
        Convert Whisper's avg_logprob to a 0-1 confidence score.
        
        avg_logprob is typically between -1.0 (low confidence) and 0.0 (high confidence)
        """
        # Sigmoid-like transformation
        # avg_logprob of 0 -> ~0.95 confidence
        # avg_logprob of -0.5 -> ~0.80 confidence  
        # avg_logprob of -1.0 -> ~0.60 confidence
        confidence = 1.0 / (1.0 + math.exp(-2 * (avg_logprob + 0.5)))
        return min(max(confidence, 0.0), 1.0)

