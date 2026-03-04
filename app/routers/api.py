import urllib.request
from fastapi import APIRouter, HTTPException, Response
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

DEMO_IMAGES = {
    "1": "https://www.smart.biz.pl/images/stories/TechBlog/app-dermatolog/demo/melanoma_wikipedia.png",
    "2": "https://www.smart.biz.pl/images/stories/TechBlog/app-dermatolog/demo/acne_vulgaris2.jpeg",
    "3": "https://www.smart.biz.pl/images/stories/TechBlog/app-dermatolog/demo/atypical-mole-irregular-borders-unusual-shape-270x203.jpg",
    "4": "https://www.smart.biz.pl/images/stories/TechBlog/app-dermatolog/demo/blue_naevus-750x560-1.jpg",
    "5": "https://www.smart.biz.pl/images/stories/TechBlog/app-dermatolog/demo/melanoma_wiki_D.jpg"

}
import base64

@router.get("/demo-data")
async def get_demo_data():
    """Return available demo images complete with base64 encoded content."""
    
    demo_items = []
    
    for k, url in DEMO_IMAGES.items():
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    continue
                    
                media_type = response.headers.get('Content-Type', '')
                if not media_type.startswith('image/'):
                    continue
                
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > 10 * 1024 * 1024:
                    continue
                    
                content = response.read(10 * 1024 * 1024 + 1)
                
                b64_content = base64.b64encode(content).decode('utf-8')
                
                demo_items.append({
                    "id": k,
                    "filename": url.split('/')[-1],
                    "mime_type": media_type,
                    "base64_data": b64_content
                })
        except Exception:
            # Skip images that fail to load
            continue
            
    return demo_items
