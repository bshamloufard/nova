"""Audio streaming endpoints."""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from config import settings

router = APIRouter()

# Reference to transcription jobs (imported from transcription module)
from api.routes.transcription import transcription_jobs


@router.get("/audio/{job_id}")
async def stream_audio(job_id: str):
    """
    Stream the audio file for a transcription job.
    
    Returns the audio file for playback in the frontend.
    """
    if job_id not in transcription_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = transcription_jobs[job_id]
    file_path = job.get("file_path")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Determine content type based on file extension
    extension = os.path.splitext(file_path)[1].lower()
    content_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }
    content_type = content_types.get(extension, "audio/mpeg")
    
    return FileResponse(
        file_path,
        media_type=content_type,
        filename=job.get("original_filename", f"{job_id}{extension}")
    )


@router.get("/audio/{job_id}/segment")
async def get_audio_segment(
    job_id: str,
    start_ms: int,
    end_ms: int
):
    """
    Get a specific segment of the audio file.
    
    Used for re-transcription of uncertain segments.
    """
    if job_id not in transcription_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = transcription_jobs[job_id]
    file_path = job.get("file_path")
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    try:
        from pydub import AudioSegment
        
        # Load audio and extract segment
        audio = AudioSegment.from_file(file_path)
        segment = audio[start_ms:end_ms]
        
        # Export to bytes
        import io
        buffer = io.BytesIO()
        segment.export(buffer, format="mp3")
        buffer.seek(0)
        
        return StreamingResponse(
            buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=segment_{start_ms}_{end_ms}.mp3"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract segment: {str(e)}")

