"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check():
    """Readiness check - verify all services are configured."""
    from config import settings
    
    services = {
        "deepgram": bool(settings.deepgram_api_key),
        "assemblyai": bool(settings.assemblyai_api_key),
        "openai": bool(settings.openai_api_key),
    }
    
    all_ready = all(services.values())
    
    return {
        "status": "ready" if all_ready else "degraded",
        "services": services
    }

