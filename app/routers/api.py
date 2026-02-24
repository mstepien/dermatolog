from fastapi import APIRouter
from app.models import HealthCheckResponse
import os

router = APIRouter(prefix="/api")

from app.services.medsiglip_service import medsiglip_service
from app.services.yolo_service import yolo_service

@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    yolo_available = yolo_service.load_model() is not None
    return HealthCheckResponse(
        status="OK",
        yolo_available=yolo_available
    )
