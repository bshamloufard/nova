"""Audio manipulation utilities."""

import os
import tempfile
from typing import Tuple
from pydub import AudioSegment


def get_audio_duration_ms(file_path: str) -> int:
    """
    Get the duration of an audio file in milliseconds.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Duration in milliseconds
    """
    audio = AudioSegment.from_file(file_path)
    return len(audio)


def extract_audio_segment(
    file_path: str,
    start_ms: int,
    end_ms: int,
    padding_ms: int = 100
) -> str:
    """
    Extract a segment from an audio file.
    
    Args:
        file_path: Path to the source audio file
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        padding_ms: Padding to add before/after for context
        
    Returns:
        Path to temporary file containing the segment
    """
    audio = AudioSegment.from_file(file_path)
    
    # Apply padding
    padded_start = max(0, start_ms - padding_ms)
    padded_end = min(len(audio), end_ms + padding_ms)
    
    # Extract segment
    segment = audio[padded_start:padded_end]
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )
    segment.export(temp_file.name, format="mp3")
    
    return temp_file.name


def convert_to_mp3(file_path: str) -> str:
    """
    Convert an audio file to MP3 format.
    
    Args:
        file_path: Path to the source audio file
        
    Returns:
        Path to the converted MP3 file
    """
    audio = AudioSegment.from_file(file_path)
    
    # Create output path
    output_path = os.path.splitext(file_path)[0] + ".mp3"
    
    # Export as MP3
    audio.export(output_path, format="mp3")
    
    return output_path


def get_audio_info(file_path: str) -> dict:
    """
    Get information about an audio file.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Dictionary with audio info
    """
    audio = AudioSegment.from_file(file_path)
    
    return {
        "duration_ms": len(audio),
        "duration_seconds": len(audio) / 1000,
        "channels": audio.channels,
        "sample_rate": audio.frame_rate,
        "sample_width": audio.sample_width,
    }


def normalize_audio(file_path: str, target_dbfs: float = -20.0) -> str:
    """
    Normalize audio volume.
    
    Args:
        file_path: Path to the source audio file
        target_dbfs: Target volume in dBFS
        
    Returns:
        Path to normalized audio file
    """
    audio = AudioSegment.from_file(file_path)
    
    # Calculate the change needed
    change_in_dbfs = target_dbfs - audio.dBFS
    
    # Apply gain
    normalized = audio + change_in_dbfs
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".mp3",
        delete=False
    )
    normalized.export(temp_file.name, format="mp3")
    
    return temp_file.name


def split_audio_into_chunks(
    file_path: str,
    chunk_duration_ms: int = 60000
) -> list[Tuple[str, int, int]]:
    """
    Split a long audio file into smaller chunks.
    
    Args:
        file_path: Path to the source audio file
        chunk_duration_ms: Duration of each chunk in milliseconds
        
    Returns:
        List of tuples (chunk_path, start_ms, end_ms)
    """
    audio = AudioSegment.from_file(file_path)
    total_duration = len(audio)
    
    chunks = []
    start_ms = 0
    
    while start_ms < total_duration:
        end_ms = min(start_ms + chunk_duration_ms, total_duration)
        chunk = audio[start_ms:end_ms]
        
        # Save chunk to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )
        chunk.export(temp_file.name, format="mp3")
        
        chunks.append((temp_file.name, start_ms, end_ms))
        start_ms = end_ms
    
    return chunks

