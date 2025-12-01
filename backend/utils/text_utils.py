"""Text processing utilities."""

import re
from typing import List


def clean_transcription_text(text: str) -> str:
    """
    Clean and normalize transcription text.
    
    Args:
        text: Raw transcription text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common punctuation issues
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s*([A-Z])', r'\1 \2', text)
    
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Split on sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def extract_numbers(text: str) -> List[dict]:
    """
    Extract numerical values from text.
    
    Args:
        text: Input text
        
    Returns:
        List of dictionaries with number info
    """
    numbers = []
    
    # Pattern for numbers with optional decimals
    pattern = r'(\d+\.?\d*)\s*(%|mg|ml|bpm|mmHg|lbs?|kg|units?|mcg)?'
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for match in matches:
        value = match.group(1)
        unit = match.group(2) if match.group(2) else None
        
        numbers.append({
            "value": value,
            "unit": unit,
            "position": match.start(),
            "raw_text": match.group(0)
        })
    
    return numbers


def find_medical_terms(text: str, terms_list: List[str]) -> List[str]:
    """
    Find medical terms in text.
    
    Args:
        text: Input text
        terms_list: List of medical terms to search for
        
    Returns:
        List of found terms
    """
    text_lower = text.lower()
    found = []
    
    for term in terms_list:
        if term.lower() in text_lower:
            found.append(term)
    
    return found


def highlight_keywords(text: str, keywords: List[str]) -> str:
    """
    Add markdown highlighting to keywords in text.
    
    Args:
        text: Input text
        keywords: Keywords to highlight
        
    Returns:
        Text with highlighted keywords
    """
    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        text = pattern.sub(f'**{keyword}**', text)
    
    return text


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def get_word_at_position(text: str, char_position: int) -> str | None:
    """
    Get the word at a specific character position.
    
    Args:
        text: Input text
        char_position: Character position
        
    Returns:
        Word at position or None
    """
    if char_position < 0 or char_position >= len(text):
        return None
    
    # Find word boundaries
    start = char_position
    while start > 0 and text[start - 1].isalnum():
        start -= 1
    
    end = char_position
    while end < len(text) and text[end].isalnum():
        end += 1
    
    word = text[start:end]
    return word if word else None

