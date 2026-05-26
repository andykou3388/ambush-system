from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """健康檢查接口"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "service": "ambush-system"
    }