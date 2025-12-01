"""Nova Transcription Tool - FastAPI Backend Entry Point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings, load_api_keys_from_file


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    # Load API keys from file if available
    load_api_keys_from_file("../api.md")
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    print(f"🚀 Nova Transcription Tool starting...")
    print(f"📁 Upload directory: {settings.upload_dir}")
    print(f"🔑 Deepgram API key: {'✓' if settings.deepgram_api_key else '✗'}")
    print(f"🔑 AssemblyAI API key: {'✓' if settings.assemblyai_api_key else '✗'}")
    print(f"🔑 OpenAI API key: {'✓' if settings.openai_api_key else '✗'}")
    
    yield
    
    # Shutdown
    print("👋 Nova Transcription Tool shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Intelligent medical transcription with multi-model orchestration",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import and include routers
from api.routes import health, transcription, audio

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(transcription.router, prefix="/api", tags=["Transcription"])
app.include_router(audio.router, prefix="/api", tags=["Audio"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

