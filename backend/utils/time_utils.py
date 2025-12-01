"""Timestamp conversion utilities."""

from typing import Tuple


def ms_to_seconds(ms: int) -> float:
    """Convert milliseconds to seconds."""
    return ms / 1000


def seconds_to_ms(seconds: float) -> int:
    """Convert seconds to milliseconds."""
    return int(seconds * 1000)


def ms_to_time_string(ms: int) -> str:
    """
    Convert milliseconds to time string (MM:SS).
    
    Args:
        ms: Time in milliseconds
        
    Returns:
        Formatted time string
    """
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


def ms_to_full_time_string(ms: int) -> str:
    """
    Convert milliseconds to full time string (HH:MM:SS.mmm).
    
    Args:
        ms: Time in milliseconds
        
    Returns:
        Formatted time string
    """
    hours = ms // 3600000
    minutes = (ms % 3600000) // 60000
    seconds = (ms % 60000) // 1000
    milliseconds = ms % 1000
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    return f"{minutes}:{seconds:02d}.{milliseconds:03d}"


def parse_time_string(time_str: str) -> int:
    """
    Parse time string to milliseconds.
    
    Supports formats:
    - MM:SS
    - HH:MM:SS
    - SS.mmm
    - MM:SS.mmm
    
    Args:
        time_str: Time string
        
    Returns:
        Time in milliseconds
    """
    parts = time_str.split(':')
    
    if len(parts) == 1:
        # Just seconds (possibly with milliseconds)
        seconds = float(parts[0])
        return int(seconds * 1000)
    
    elif len(parts) == 2:
        # MM:SS or MM:SS.mmm
        minutes = int(parts[0])
        seconds_parts = parts[1].split('.')
        seconds = int(seconds_parts[0])
        ms = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        return (minutes * 60 + seconds) * 1000 + ms
    
    elif len(parts) == 3:
        # HH:MM:SS or HH:MM:SS.mmm
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        ms = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        return (hours * 3600 + minutes * 60 + seconds) * 1000 + ms
    
    raise ValueError(f"Invalid time string format: {time_str}")


def get_time_range_string(start_ms: int, end_ms: int) -> str:
    """
    Get a formatted time range string.
    
    Args:
        start_ms: Start time in milliseconds
        end_ms: End time in milliseconds
        
    Returns:
        Formatted range string (e.g., "0:45 - 1:23")
    """
    return f"{ms_to_time_string(start_ms)} - {ms_to_time_string(end_ms)}"


def calculate_duration(start_ms: int, end_ms: int) -> int:
    """Calculate duration between two timestamps."""
    return end_ms - start_ms


def overlap_time_ranges(
    range1: Tuple[int, int],
    range2: Tuple[int, int]
) -> Tuple[int, int] | None:
    """
    Calculate the overlap between two time ranges.
    
    Args:
        range1: First range (start_ms, end_ms)
        range2: Second range (start_ms, end_ms)
        
    Returns:
        Overlap range or None if no overlap
    """
    start = max(range1[0], range2[0])
    end = min(range1[1], range2[1])
    
    if start < end:
        return (start, end)
    return None


def merge_time_ranges(ranges: list[Tuple[int, int]]) -> list[Tuple[int, int]]:
    """
    Merge overlapping time ranges.
    
    Args:
        ranges: List of (start_ms, end_ms) tuples
        
    Returns:
        List of merged ranges
    """
    if not ranges:
        return []
    
    # Sort by start time
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    
    merged = [sorted_ranges[0]]
    
    for current in sorted_ranges[1:]:
        last = merged[-1]
        
        # Check if ranges overlap or are adjacent
        if current[0] <= last[1]:
            # Merge
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    
    return merged

