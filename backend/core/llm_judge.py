"""LLM Judge for evaluating transcription candidates."""

import json
from typing import Dict, Optional
from openai import AsyncOpenAI

from models.segment import UncertainSegment, OrchestratorDecision, CandidateTranscription
from models.transcription import TranscriptionResult


class LLMJudge:
    """
    Uses an LLM to determine the best transcription for uncertain segments.
    
    CRITICAL: The judge should prefer selecting an existing transcription
    over synthesizing a new one. Synthesis is the ABSOLUTE LAST RESORT.
    """
    
    JUDGE_SYSTEM_PROMPT = """You are an expert medical transcription reviewer. Your task is to evaluate multiple transcription candidates for an audio segment where the primary transcription model had low confidence.

CRITICAL INSTRUCTION: You must STRONGLY PREFER selecting one of the provided transcriptions over creating your own. Your primary job is to CHOOSE, not to CREATE.

You will be given:
1. Context BEFORE the uncertain segment (preceding words in the conversation)
2. Context AFTER the uncertain segment (following words in the conversation)
3. Multiple transcription candidates from different speech-to-text models
4. Confidence scores from each model

DECISION PRIORITY (follow this order strictly):
1. FIRST: Check if any transcription makes clear sense in context → SELECT IT
2. SECOND: If multiple make sense, choose the one with highest confidence → SELECT IT
3. THIRD: If transcriptions differ slightly but are similar, select the most complete one → SELECT IT
4. FOURTH: If transcriptions differ significantly, use context to determine which fits → SELECT IT
5. LAST RESORT ONLY: If ALL transcriptions are clearly wrong, nonsensical, or completely contradict the context in ways that cannot be explained → SYNTHESIZE your own

When synthesizing (ONLY as last resort), you must:
- Base it on the phonetic similarities between candidates
- Ensure it fits the medical/clinical context perfectly
- Provide detailed justification for why ALL candidates were rejected

Your response must be valid JSON with this exact structure:
{
    "chosen_source": "deepgram" | "assemblyai" | "whisper" | "synthesized",
    "final_text": "the selected or synthesized text",
    "reasoning": "Brief explanation of your decision",
    "confidence_boost": 0.85,
    "synthesis_justification": "Only if synthesized - why ALL candidates were wrong"
}"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the LLM Judge.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o for best reasoning)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def evaluate(
        self,
        segment: UncertainSegment,
        candidates: Dict[str, TranscriptionResult]
    ) -> OrchestratorDecision:
        """
        Evaluate transcription candidates and return a decision.
        
        Args:
            segment: The uncertain segment being evaluated
            candidates: Dict of model_name -> TranscriptionResult
            
        Returns:
            OrchestratorDecision with chosen source and reasoning
        """
        # Format the evaluation prompt
        user_prompt = self._format_evaluation_prompt(segment, candidates)
        
        # Call the LLM
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent decisions
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        return self._parse_response(
            response.choices[0].message.content,
            segment,
            candidates
        )
    
    def _format_evaluation_prompt(
        self,
        segment: UncertainSegment,
        candidates: Dict[str, TranscriptionResult]
    ) -> str:
        """Format the prompt for LLM evaluation."""
        
        # Get candidate texts and confidences
        deepgram_result = candidates.get("deepgram")
        assemblyai_result = candidates.get("assemblyai")
        whisper_result = candidates.get("whisper")
        
        deepgram_text = deepgram_result.full_text if deepgram_result else "Error - no transcription"
        deepgram_conf = deepgram_result.overall_confidence if deepgram_result else "N/A"
        
        assemblyai_text = assemblyai_result.full_text if assemblyai_result else "Error - no transcription"
        assemblyai_conf = assemblyai_result.overall_confidence if assemblyai_result else "N/A"
        
        whisper_text = whisper_result.full_text if whisper_result else "Error - no transcription"
        whisper_conf = whisper_result.overall_confidence if whisper_result else "N/A"
        
        prompt = f"""
CONTEXT BEFORE (preceding words):
"{segment.context_before}"

UNCERTAIN SEGMENT (timestamps: {segment.start_time_ms}ms - {segment.end_time_ms}ms):
[This is where the transcription is uncertain]

CONTEXT AFTER (following words):
"{segment.context_after}"

TRANSCRIPTION CANDIDATES:

1. DEEPGRAM (confidence: {deepgram_conf}):
"{deepgram_text}"

2. ASSEMBLYAI (confidence: {assemblyai_conf}):
"{assemblyai_text}"

3. WHISPER (confidence: {whisper_conf}):
"{whisper_text}"

Based on the context and candidates above, determine the best transcription.
Remember: STRONGLY prefer selecting an existing transcription over synthesizing.

Respond with valid JSON only.
"""
        return prompt
    
    def _parse_response(
        self,
        response_text: str,
        segment: UncertainSegment,
        candidates: Dict[str, TranscriptionResult]
    ) -> OrchestratorDecision:
        """Parse LLM response into OrchestratorDecision."""
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group())
                except:
                    data = self._fallback_decision(segment, candidates)
            else:
                data = self._fallback_decision(segment, candidates)
        
        chosen_source = data.get("chosen_source", "deepgram").lower()
        final_text = data.get("final_text", segment.original_text)
        reasoning = data.get("reasoning", "Automatic selection")
        confidence_boost = float(data.get("confidence_boost", 0.8))
        synthesis_justification = data.get("synthesis_justification")
        
        # Validate chosen_source
        valid_sources = ["deepgram", "assemblyai", "whisper", "synthesized"]
        if chosen_source not in valid_sources:
            chosen_source = "deepgram"
        
        # Build candidate transcriptions dict
        candidate_transcriptions = {}
        for name, result in candidates.items():
            if result:
                candidate_transcriptions[name] = CandidateTranscription(
                    model_name=name,
                    text=result.full_text,
                    confidence=result.overall_confidence,
                    words=result.words
                )
        
        return OrchestratorDecision(
            segment=segment,
            candidate_transcriptions=candidate_transcriptions,
            chosen_source=chosen_source,
            final_text=final_text,
            reasoning=reasoning,
            confidence_boost=confidence_boost,
            was_synthesized=chosen_source == "synthesized",
            synthesis_justification=synthesis_justification
        )
    
    def _fallback_decision(
        self,
        segment: UncertainSegment,
        candidates: Dict[str, TranscriptionResult]
    ) -> dict:
        """
        Fallback decision when LLM response is invalid.
        Selects the candidate with highest confidence.
        """
        best_source = "deepgram"
        best_confidence = 0.0
        best_text = segment.original_text
        
        for name, result in candidates.items():
            if result and result.overall_confidence > best_confidence:
                best_source = name
                best_confidence = result.overall_confidence
                best_text = result.full_text
        
        return {
            "chosen_source": best_source,
            "final_text": best_text,
            "reasoning": "Automatic fallback: selected highest confidence",
            "confidence_boost": min(best_confidence + 0.1, 1.0),
            "synthesis_justification": None
        }

