"""Clinical data extraction from transcriptions."""

import re
from typing import List, Tuple, Optional

from models.transcription import TranscriptionResult
from models.clinical_data import (
    ActionItem, NumericalValue, ClinicalExtraction,
    ActionItemCategory, ActionItemPriority, NumericalCategory
)


class ClinicalExtractor:
    """
    Extracts clinically relevant information from transcription.
    Uses pattern matching and keyword detection for identification.
    """
    
    # Numerical patterns for vitals, labs, and measurements
    VITAL_PATTERNS = [
        # Blood pressure patterns
        (r"blood pressure[:\s]+(\d{2,3})[/\\](\d{2,3})", "blood_pressure", NumericalCategory.VITAL, "mmHg"),
        (r"bp[:\s]+(\d{2,3})[/\\](\d{2,3})", "blood_pressure", NumericalCategory.VITAL, "mmHg"),
        (r"(\d{2,3})[/\\](\d{2,3})(?:\s*mm\s*hg|\s*millimeters)", "blood_pressure", NumericalCategory.VITAL, "mmHg"),
        
        # Heart rate patterns
        (r"heart rate[:\s]+(\d{2,3})", "heart_rate", NumericalCategory.VITAL, "bpm"),
        (r"pulse[:\s]+(\d{2,3})", "pulse", NumericalCategory.VITAL, "bpm"),
        (r"hr[:\s]+(\d{2,3})", "heart_rate", NumericalCategory.VITAL, "bpm"),
        
        # Temperature patterns
        (r"temperature[:\s]+(\d{2,3}\.?\d?)", "temperature", NumericalCategory.VITAL, "°F"),
        (r"temp[:\s]+(\d{2,3}\.?\d?)", "temperature", NumericalCategory.VITAL, "°F"),
        (r"(\d{2,3}\.?\d?)(?:\s*degrees|\s*fahrenheit|\s*celsius)", "temperature", NumericalCategory.VITAL, "°"),
        
        # Weight patterns
        (r"weight[:\s]+(\d{2,3})[\s]*(lbs?|pounds?|kg|kilograms?)?", "weight", NumericalCategory.MEASUREMENT, None),
        (r"weighs?[\s]+(\d{2,3})[\s]*(lbs?|pounds?|kg|kilograms?)?", "weight", NumericalCategory.MEASUREMENT, None),
        
        # Lab values
        (r"a1c[:\s]+(\d\.?\d?)[\s]*%?", "a1c", NumericalCategory.LAB, "%"),
        (r"hemoglobin a1c[:\s]+(\d\.?\d?)", "a1c", NumericalCategory.LAB, "%"),
        (r"hba1c[:\s]+(\d\.?\d?)", "a1c", NumericalCategory.LAB, "%"),
        (r"cholesterol[:\s]+(\d{2,3})", "cholesterol", NumericalCategory.LAB, "mg/dL"),
        (r"glucose[:\s]+(\d{2,3})", "glucose", NumericalCategory.LAB, "mg/dL"),
        (r"blood sugar[:\s]+(\d{2,3})", "blood_sugar", NumericalCategory.LAB, "mg/dL"),
        (r"creatinine[:\s]+(\d\.?\d{1,2})", "creatinine", NumericalCategory.LAB, "mg/dL"),
        
        # Oxygen saturation
        (r"oxygen[:\s]+(\d{2,3})[\s]*%?", "oxygen_saturation", NumericalCategory.VITAL, "%"),
        (r"o2[:\s]+(\d{2,3})[\s]*%?", "oxygen_saturation", NumericalCategory.VITAL, "%"),
        (r"sat[:\s]+(\d{2,3})[\s]*%?", "oxygen_saturation", NumericalCategory.VITAL, "%"),
        (r"spo2[:\s]+(\d{2,3})", "oxygen_saturation", NumericalCategory.VITAL, "%"),
        
        # Dosage patterns
        (r"(\d+)[\s]*(?:mg|milligrams?)", "dosage", NumericalCategory.DOSAGE, "mg"),
        (r"(\d+)[\s]*(?:ml|milliliters?)", "dosage", NumericalCategory.DOSAGE, "ml"),
        (r"(\d+)[\s]*(?:mcg|micrograms?)", "dosage", NumericalCategory.DOSAGE, "mcg"),
        (r"(\d+)[\s]*(?:units?)", "dosage", NumericalCategory.DOSAGE, "units"),
    ]
    
    # Action item keywords by category
    ACTION_KEYWORDS = {
        ActionItemCategory.PRESCRIPTION: [
            "prescribe", "prescription", "rx", "medication", "refill",
            "start", "continue", "discontinue", "increase", "decrease",
            "titrate", "taper", "drug", "medicine"
        ],
        ActionItemCategory.FOLLOW_UP: [
            "follow up", "follow-up", "return", "schedule", "appointment",
            "come back", "see me", "weeks", "months", "check in",
            "revisit", "recheck"
        ],
        ActionItemCategory.REFERRAL: [
            "refer", "referral", "specialist", "consult", "consultation",
            "see a", "cardiologist", "neurologist", "dermatologist",
            "orthopedic", "oncologist", "psychiatrist", "surgeon"
        ],
        ActionItemCategory.TEST: [
            "test", "lab", "labs", "bloodwork", "imaging", "x-ray",
            "xray", "mri", "ct scan", "ct", "ultrasound", "ecg", "ekg",
            "echocardiogram", "biopsy", "culture", "panel", "screening"
        ],
    }
    
    # Medical terminology list
    MEDICAL_TERMS = [
        "hypertension", "hypotension", "diabetes", "diabetic", "mellitus",
        "cardiovascular", "coronary", "arrhythmia", "tachycardia", "bradycardia",
        "pneumonia", "bronchitis", "asthma", "copd", "emphysema",
        "arthritis", "osteoporosis", "fracture", "inflammation",
        "infection", "antibiotic", "viral", "bacterial",
        "diagnosis", "prognosis", "symptom", "syndrome", "chronic", "acute",
        "benign", "malignant", "metastatic", "tumor", "lesion",
        "edema", "anemia", "neuropathy", "nephropathy", "retinopathy",
        "hypothyroid", "hyperthyroid", "thyroid",
        "cholesterol", "triglycerides", "ldl", "hdl",
        "insulin", "metformin", "lisinopril", "atorvastatin",
        "amlodipine", "omeprazole", "levothyroxine", "gabapentin"
    ]
    
    def extract(self, transcription: TranscriptionResult) -> ClinicalExtraction:
        """
        Extract all clinical data from transcription.
        
        Args:
            transcription: The transcription result to analyze
            
        Returns:
            ClinicalExtraction with action items, numerical values, etc.
        """
        full_text = transcription.full_text.lower()
        
        numerical_values = self._extract_numerical_values(transcription)
        action_items = self._extract_action_items(transcription)
        medical_terms = self._extract_medical_terms(full_text)
        important_phrases = self._extract_important_phrases(transcription)
        
        return ClinicalExtraction(
            action_items=action_items,
            numerical_values=numerical_values,
            important_phrases=important_phrases,
            medical_terms=medical_terms
        )
    
    def _extract_numerical_values(
        self,
        transcription: TranscriptionResult
    ) -> List[NumericalValue]:
        """Extract numerical values using regex patterns."""
        values = []
        full_text = transcription.full_text.lower()
        seen_values = set()  # Avoid duplicates
        
        for pattern, label, category, unit in self.VITAL_PATTERNS:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                # Get the primary value (first capture group)
                value = match.group(1)
                
                # For blood pressure, combine systolic/diastolic
                if label == "blood_pressure" and len(match.groups()) >= 2:
                    value = f"{match.group(1)}/{match.group(2)}"
                
                # Detect unit from match if pattern supports it
                detected_unit = unit
                if len(match.groups()) >= 2 and label in ["weight", "dosage"]:
                    matched_unit = match.group(2)
                    if matched_unit:
                        detected_unit = matched_unit.lower()
                
                # Find timestamp for this match
                timestamp_ms = self._find_timestamp_for_position(
                    transcription,
                    match.start()
                )
                
                # Create unique key to avoid duplicates
                key = f"{label}:{value}:{timestamp_ms}"
                if key in seen_values:
                    continue
                seen_values.add(key)
                
                values.append(NumericalValue(
                    value=value,
                    unit=detected_unit,
                    category=category,
                    label=label.replace("_", " ").title(),
                    timestamp_ms=timestamp_ms,
                    related_segment_index=0,
                    raw_text=match.group(0)
                ))
        
        return values
    
    def _extract_action_items(
        self,
        transcription: TranscriptionResult
    ) -> List[ActionItem]:
        """Extract action items from transcription."""
        items = []
        full_text = transcription.full_text.lower()
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', transcription.full_text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if not sentence_lower:
                continue
            
            # Check each category's keywords
            for category, keywords in self.ACTION_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in sentence_lower:
                        # Find timestamp
                        pos = full_text.find(sentence_lower[:20])
                        timestamp_ms = self._find_timestamp_for_position(
                            transcription, max(0, pos)
                        )
                        
                        # Determine priority
                        priority = self._determine_priority(sentence_lower)
                        
                        items.append(ActionItem(
                            text=sentence.strip(),
                            category=category,
                            priority=priority,
                            timestamp_ms=timestamp_ms,
                            related_segment_index=0,
                            keywords=[keyword]
                        ))
                        break  # Only add once per sentence per category
        
        # Remove duplicate action items
        seen = set()
        unique_items = []
        for item in items:
            key = item.text[:50]
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items
    
    def _extract_medical_terms(self, full_text: str) -> List[str]:
        """Extract recognized medical terminology."""
        found_terms = []
        full_text_lower = full_text.lower()
        
        for term in self.MEDICAL_TERMS:
            if term in full_text_lower:
                found_terms.append(term)
        
        return list(set(found_terms))
    
    def _extract_important_phrases(
        self,
        transcription: TranscriptionResult
    ) -> List[str]:
        """Extract important clinical phrases."""
        important_patterns = [
            r"patient (?:reports?|states?|complains? of|presents? with) .{10,100}",
            r"diagnosed with .{5,50}",
            r"history of .{5,50}",
            r"allergic to .{5,50}",
            r"no known .{5,30}",
            r"family history .{5,50}",
            r"recommend(?:s|ed|ing)? .{5,100}",
            r"concern(?:s|ed)? (?:about|for|regarding) .{5,50}",
        ]
        
        phrases = []
        full_text = transcription.full_text
        
        for pattern in important_patterns:
            matches = re.finditer(pattern, full_text, re.IGNORECASE)
            for match in matches:
                phrase = match.group(0).strip()
                if phrase and len(phrase) > 10:
                    phrases.append(phrase)
        
        return phrases[:20]  # Limit to 20 phrases
    
    def _find_timestamp_for_position(
        self,
        transcription: TranscriptionResult,
        char_position: int
    ) -> int:
        """
        Find the timestamp for a character position in the text.
        
        Args:
            transcription: Transcription with word-level timestamps
            char_position: Character position in full_text
            
        Returns:
            Timestamp in milliseconds
        """
        if not transcription.words:
            return 0
        
        # Build character offset map
        current_pos = 0
        for word in transcription.words:
            word_end_pos = current_pos + len(word.text) + 1  # +1 for space
            if char_position <= word_end_pos:
                return word.start_time_ms
            current_pos = word_end_pos
        
        # Default to last word
        return transcription.words[-1].start_time_ms
    
    def _determine_priority(self, sentence: str) -> ActionItemPriority:
        """
        Determine priority level for an action item.
        
        Args:
            sentence: The sentence containing the action item
            
        Returns:
            Priority level
        """
        high_priority_terms = [
            "urgent", "immediately", "emergency", "asap", "critical",
            "today", "right away", "stat", "concerning", "worrisome"
        ]
        
        low_priority_terms = [
            "optional", "consider", "if possible", "when convenient",
            "routine", "annual", "yearly"
        ]
        
        sentence_lower = sentence.lower()
        
        for term in high_priority_terms:
            if term in sentence_lower:
                return ActionItemPriority.HIGH
        
        for term in low_priority_terms:
            if term in sentence_lower:
                return ActionItemPriority.LOW
        
        return ActionItemPriority.MEDIUM

