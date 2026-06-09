from fastapi import APIRouter

from config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "helmos-api",
        "openrouter_configured": bool(settings.openrouter_api_key),
    }
