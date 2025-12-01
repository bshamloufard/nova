"""Transcription API endpoints."""

import os
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel

from config import settings

router = APIRouter()

# In-memory job storage (would use database in production)
transcription_jobs: dict = {}


class TranscriptionJobResponse(BaseModel):
    """Response model for transcription job creation."""
    job_id: str
    status: str
    message: str


class TranscriptionStatusResponse(BaseModel):
    """Response model for transcription status."""
    job_id: str
    status: str
    progress: Optional[float] = None
    error: Optional[str] = None


@router.post("/transcribe", response_model=TranscriptionJobResponse)
async def upload_and_transcribe(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload an audio file and start transcription.
    
    Accepts MP3 files up to 100MB.
    Returns a job ID for tracking progress.
    """
    # Validate file type
    if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported formats: MP3, WAV, M4A, OGG"
        )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join(settings.upload_dir, f"{job_id}{file_extension}")
    
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    try:
        contents = await file.read()
        
        # Check file size
        file_size_mb = len(contents) / (1024 * 1024)
        if file_size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
            )
        
        with open(file_path, "wb") as f:
            f.write(contents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Initialize job status
    transcription_jobs[job_id] = {
        "status": "pending",
        "progress": 0.0,
        "file_path": file_path,
        "original_filename": file.filename,
        "result": None,
        "error": None,
    }
    
    # Start transcription in background
    background_tasks.add_task(process_transcription, job_id, file_path)
    
    return TranscriptionJobResponse(
        job_id=job_id,
        status="pending",
        message="Transcription job started"
    )


async def process_transcription(job_id: str, file_path: str):
    """Background task to process transcription."""
    from core.orchestrator import TranscriptionOrchestrator
    from services.transcription.deepgram import DeepgramService
    from services.transcription.assemblyai import AssemblyAIService
    from services.transcription.whisper import WhisperService
    from core.llm_judge import LLMJudge
    from services.clinical_extractor import ClinicalExtractor
    from services.timeline_generator import TimelineGenerator
    
    try:
        transcription_jobs[job_id]["status"] = "processing"
        transcription_jobs[job_id]["progress"] = 0.1
        
        # Initialize services
        deepgram_service = DeepgramService(settings.deepgram_api_key)
        assemblyai_service = AssemblyAIService(settings.assemblyai_api_key)
        whisper_service = WhisperService(settings.openai_api_key)
        llm_judge = LLMJudge(settings.openai_api_key)
        
        # Create orchestrator
        orchestrator = TranscriptionOrchestrator(
            deepgram_service=deepgram_service,
            assemblyai_service=assemblyai_service,
            whisper_service=whisper_service,
            llm_judge=llm_judge,
            confidence_threshold=settings.confidence_threshold
        )
        
        transcription_jobs[job_id]["progress"] = 0.2
        
        # Process audio through orchestrator
        transcription_result, orchestrator_decisions = await orchestrator.process_audio(
            file_path
        )
        
        transcription_jobs[job_id]["progress"] = 0.7
        
        # Extract clinical data
        clinical_extractor = ClinicalExtractor()
        clinical_data = clinical_extractor.extract(transcription_result)
        
        transcription_jobs[job_id]["progress"] = 0.85
        
        # Generate timeline
        timeline_generator = TimelineGenerator()
        timeline_data = timeline_generator.generate(
            transcription_result,
            orchestrator_decisions,
            clinical_data
        )
        
        transcription_jobs[job_id]["progress"] = 1.0
        transcription_jobs[job_id]["status"] = "completed"
        transcription_jobs[job_id]["result"] = {
            "transcription": transcription_result.model_dump(),
            "orchestrator_decisions": [d.model_dump() for d in orchestrator_decisions],
            "clinical_data": clinical_data.model_dump(),
            "timeline": timeline_data.model_dump(),
        }
        
    except Exception as e:
        transcription_jobs[job_id]["status"] = "failed"
        transcription_jobs[job_id]["error"] = str(e)
        import traceback
        traceback.print_exc()


@router.get("/transcription/{job_id}/status", response_model=TranscriptionStatusResponse)
async def get_transcription_status(job_id: str):
    """Get the status of a transcription job."""
    if job_id not in transcription_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = transcription_jobs[job_id]
    
    return TranscriptionStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        error=job.get("error")
    )


@router.get("/transcription/{job_id}")
async def get_transcription_result(job_id: str):
    """Get the full transcription result."""
    if job_id not in transcription_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = transcription_jobs[job_id]
    
    if job["status"] == "failed":
        raise HTTPException(status_code=500, detail=job.get("error", "Transcription failed"))
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=202,
            detail=f"Transcription not yet complete. Status: {job['status']}"
        )
    
    return {
        "job_id": job_id,
        "status": "completed",
        "result": job["result"]
    }

