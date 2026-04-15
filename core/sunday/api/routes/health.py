"""Health check endpoints."""

from fastapi import APIRouter

from sunday.config.constants import APP_NAME, APP_VERSION
from sunday.core.llm.router import llm_router
from sunday.core.voice import stt, tts, vad

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check — is the server running?"""
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health — checks all subsystems."""
    llm_status = await llm_router.health()

    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "subsystems": {
            "llm": llm_status,
            "tts": "available" if tts.is_available() else "unavailable",
            "stt": "available" if stt.is_available() else "unavailable",
            "vad": "available" if vad.is_available() else "unavailable",
        },
    }
