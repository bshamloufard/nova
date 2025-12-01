"""Multi-model transcription orchestrator."""

import asyncio
from typing import List, Tuple, Optional

from models.transcription import TranscriptionResult, Word
from models.segment import UncertainSegment, OrchestratorDecision
from services.transcription.deepgram import DeepgramService
from services.transcription.assemblyai import AssemblyAIService
from services.transcription.whisper import WhisperService
from core.confidence_analyzer import ConfidenceAnalyzer
from core.llm_judge import LLMJudge


class TranscriptionOrchestrator:
    """
    Orchestrates multiple transcription models for uncertain audio segments.
    
    CRITICAL DESIGN PRINCIPLE:
    The LLM judge should SELECT from existing transcriptions whenever possible.
    Synthesizing a new transcription is the LAST RESORT and should only happen
    when ALL candidate transcriptions are clearly incorrect or nonsensical.
    """
    
    def __init__(
        self,
        deepgram_service: DeepgramService,
        assemblyai_service: AssemblyAIService,
        whisper_service: WhisperService,
        llm_judge: LLMJudge,
        confidence_threshold: float = 0.75,
        context_window_words: int = 50
    ):
        """
        Initialize the orchestrator with transcription services.
        
        Args:
            deepgram_service: Deepgram transcription service
            assemblyai_service: AssemblyAI transcription service
            whisper_service: OpenAI Whisper transcription service
            llm_judge: LLM judge for evaluating candidates
            confidence_threshold: Threshold below which to trigger orchestration
            context_window_words: Number of context words for LLM
        """
        self.services = {
            "deepgram": deepgram_service,
            "assemblyai": assemblyai_service,
            "whisper": whisper_service
        }
        self.llm_judge = llm_judge
        self.confidence_threshold = confidence_threshold
        
        self.confidence_analyzer = ConfidenceAnalyzer(
            confidence_threshold=confidence_threshold,
            context_window_words=context_window_words
        )
    
    async def process_audio(
        self,
        audio_file_path: str,
        medical_vocabulary: Optional[List[str]] = None
    ) -> Tuple[TranscriptionResult, List[OrchestratorDecision]]:
        """
        Main entry point for processing an audio file.
        
        1. Primary transcription with Deepgram (fastest, most accurate)
        2. Identify uncertain segments via confidence analysis
        3. For uncertain segments, invoke all 3 models
        4. Use LLM judge to select best transcription
        5. Merge decisions back into final transcript
        
        Args:
            audio_file_path: Path to the audio file
            medical_vocabulary: Optional list of medical terms for boosting
            
        Returns:
            Tuple of (final transcription, list of orchestrator decisions)
        """
        # Default medical vocabulary for clinical context
        if medical_vocabulary is None:
            medical_vocabulary = [
                "hypertension", "diabetes", "cholesterol", "hemoglobin",
                "prescription", "medication", "diagnosis", "symptoms",
                "blood pressure", "heart rate", "temperature", "oxygen",
                "milligrams", "milliliters", "units", "dosage"
            ]
        
        # Step 1: Primary transcription with Deepgram
        print("Step 1: Primary transcription with Deepgram...")
        primary_result = await self.services["deepgram"].transcribe(
            audio_file_path,
            vocabulary_boost=medical_vocabulary
        )
        
        # Step 2: Identify uncertain segments
        print("Step 2: Analyzing confidence levels...")
        uncertain_segments = self.confidence_analyzer.identify_uncertain_segments(
            primary_result
        )
        
        print(f"Found {len(uncertain_segments)} uncertain segment(s)")
        
        if not uncertain_segments:
            # No uncertain segments, return primary result
            return primary_result, []
        
        # Step 3: Process each uncertain segment through the council
        print("Step 3: Processing uncertain segments with multi-model orchestration...")
        decisions = await self._process_uncertain_segments(
            audio_file_path,
            uncertain_segments
        )
        
        # Step 4: Merge decisions back into final transcript
        print("Step 4: Merging orchestrated decisions...")
        final_result = self._merge_decisions(primary_result, decisions)
        
        return final_result, decisions
    
    async def _process_uncertain_segments(
        self,
        audio_file_path: str,
        segments: List[UncertainSegment]
    ) -> List[OrchestratorDecision]:
        """
        For each uncertain segment, invoke all models and get LLM judgment.
        
        Args:
            audio_file_path: Path to audio file
            segments: List of uncertain segments
            
        Returns:
            List of OrchestratorDecision for each segment
        """
        decisions = []
        
        for i, segment in enumerate(segments):
            print(f"  Processing segment {i+1}/{len(segments)} ({segment.start_time_ms}ms - {segment.end_time_ms}ms)...")
            
            # Get transcriptions from all models concurrently
            candidate_results = await self._get_all_transcriptions(
                audio_file_path,
                segment
            )
            
            # Get LLM judgment
            decision = await self.llm_judge.evaluate(
                segment=segment,
                candidates=candidate_results
            )
            
            print(f"    Chosen source: {decision.chosen_source}")
            print(f"    Final text: {decision.final_text[:50]}..." if len(decision.final_text) > 50 else f"    Final text: {decision.final_text}")
            
            decisions.append(decision)
        
        return decisions
    
    async def _get_all_transcriptions(
        self,
        audio_file_path: str,
        segment: UncertainSegment
    ) -> dict:
        """
        Get transcriptions from all models for a segment.
        Runs concurrently for speed.
        
        Args:
            audio_file_path: Path to audio file
            segment: The uncertain segment
            
        Returns:
            Dict of model_name -> TranscriptionResult
        """
        results = {}
        
        # Create tasks for all services
        tasks = {}
        for name, service in self.services.items():
            tasks[name] = service.transcribe_segment(
                audio_file_path,
                segment.start_time_ms,
                segment.end_time_ms
            )
        
        # Execute concurrently
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                print(f"    Warning: {name} transcription failed: {e}")
                results[name] = None
        
        return results
    
    def _merge_decisions(
        self,
        primary_result: TranscriptionResult,
        decisions: List[OrchestratorDecision]
    ) -> TranscriptionResult:
        """
        Merge orchestrator decisions back into the primary transcription.
        
        Replaces words in uncertain segments with the chosen transcription.
        
        Args:
            primary_result: Original primary transcription
            decisions: List of orchestrator decisions
            
        Returns:
            Updated TranscriptionResult with merged decisions
        """
        if not decisions:
            return primary_result
        
        # Create a new word list with merged results
        merged_words = []
        decision_index = 0
        i = 0
        
        while i < len(primary_result.words):
            word = primary_result.words[i]
            
            # Check if this word falls within an orchestrated segment
            if decision_index < len(decisions):
                decision = decisions[decision_index]
                segment = decision.segment
                
                # Check if current word is within the segment
                if (word.start_time_ms >= segment.start_time_ms and
                    word.end_time_ms <= segment.end_time_ms):
                    
                    # Find the candidate that was chosen
                    chosen_source = decision.chosen_source
                    
                    if chosen_source == "synthesized":
                        # Use synthesized text - create words with estimated timestamps
                        synthesized_words = self._create_words_from_text(
                            decision.final_text,
                            segment.start_time_ms,
                            segment.end_time_ms,
                            decision.confidence_boost
                        )
                        merged_words.extend(synthesized_words)
                    elif chosen_source in decision.candidate_transcriptions:
                        # Use words from chosen candidate
                        candidate = decision.candidate_transcriptions[chosen_source]
                        for cw in candidate.words:
                            # Boost confidence based on orchestration
                            boosted_word = Word(
                                text=cw.text,
                                start_time_ms=cw.start_time_ms,
                                end_time_ms=cw.end_time_ms,
                                confidence=decision.confidence_boost,
                                speaker=cw.speaker
                            )
                            merged_words.append(boosted_word)
                    else:
                        # Fallback: use original words with boosted confidence
                        for ow in segment.original_words:
                            boosted_word = Word(
                                text=ow.text,
                                start_time_ms=ow.start_time_ms,
                                end_time_ms=ow.end_time_ms,
                                confidence=decision.confidence_boost,
                                speaker=ow.speaker
                            )
                            merged_words.append(boosted_word)
                    
                    # Skip all words in this segment
                    while (i < len(primary_result.words) and
                           primary_result.words[i].end_time_ms <= segment.end_time_ms):
                        i += 1
                    
                    decision_index += 1
                    continue
            
            # Word is not in any orchestrated segment, keep as-is
            merged_words.append(word)
            i += 1
        
        # Rebuild full text from merged words
        full_text = " ".join(w.text for w in merged_words)
        
        # Calculate new overall confidence
        if merged_words:
            overall_confidence = sum(w.confidence for w in merged_words) / len(merged_words)
        else:
            overall_confidence = primary_result.overall_confidence
        
        return TranscriptionResult(
            full_text=full_text,
            words=merged_words,
            overall_confidence=overall_confidence,
            duration_ms=primary_result.duration_ms,
            language=primary_result.language,
            model_name="orchestrated",
            raw_response=None
        )
    
    def _create_words_from_text(
        self,
        text: str,
        start_ms: int,
        end_ms: int,
        confidence: float
    ) -> List[Word]:
        """
        Create Word objects from synthesized text with estimated timestamps.
        
        Args:
            text: The synthesized text
            start_ms: Segment start time
            end_ms: Segment end time
            confidence: Confidence to assign
            
        Returns:
            List of Word objects
        """
        words_list = text.split()
        if not words_list:
            return []
        
        duration = end_ms - start_ms
        word_duration = duration / len(words_list)
        
        result = []
        for i, word_text in enumerate(words_list):
            word_start = int(start_ms + i * word_duration)
            word_end = int(word_start + word_duration)
            
            result.append(Word(
                text=word_text,
                start_time_ms=word_start,
                end_time_ms=word_end,
                confidence=confidence,
                speaker=None
            ))
        
        return result

