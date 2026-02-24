import uuid
import base64
import logging
import io
import json
import os
import time
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Response, Request
from PIL import Image


from app.models import TimelineItem, Photo, SinglePhotoAnalysisRequest, SinglePhotoAnalysisResponse, SaliencyRequest, SaliencyResponse
from app.services.medsiglip_service import medsiglip_service
from app.services.medsiglip_modality_wrapper import (
    medsiglip_wrapped_service, 
)
from app.services.image_preprocess_service import image_preprocess_service, PreprocessStrategy
from app.services.result_interpreter import result_interpreter
from app.dal.photo_repo import photo_repo

router = APIRouter(prefix="/api/photos", tags=["photos"])

logger = logging.getLogger(__name__)

def get_date_from_image(image_bytes: bytes) -> str:
    """Heuristic to find creation date from EXIF or return today."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        exif = image._getexif()
        if exif:
            # 36867 is DateTimeOriginal, 306 is DateTime
            for tag_id in [36867, 306]:
                if tag_id in exif:
                    date_str = exif[tag_id]
                    # Format is usually "YYYY:MM:DD HH:MM:SS"
                    try:
                        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        return dt.date().isoformat()
                    except ValueError:
                        continue
    except Exception as e:
        logger.warning(f"Failed to extract EXIF: {e}")
    
    # Fallback to today
    return date.today().isoformat()

import hashlib

@router.post("/upload")
async def upload_photos(
    request: Request,
    files: List[UploadFile] = File(...),
):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found - reload page")

    processed_ids = []
    skipped_count = 0
    
    try:
        for file in files:
            content = await file.read()
            
            # Calculate MD5 hash
            file_hash = hashlib.md5(content).hexdigest()
            
            # Check for duplicate in this session
            existing_id = photo_repo.find_duplicate(session_id, file_hash)
            
            if existing_id:
                skipped_count += 1
                continue

            # Heuristic Date Extraction
            creation_date = get_date_from_image(content)
            
            photo_id = str(uuid.uuid4())
            
            # Use original extension or default to .jpg
            ext = os.path.splitext(file.filename)[1]
            if not ext:
                ext = ".jpg"

            # Save metadata and binary content to Repo
            photo_repo.create_photo(photo_id, session_id, file.filename, ext, creation_date, file_hash, content)
            
            processed_ids.append(photo_id)
                
        return {
            "uploaded": len(processed_ids), 
            "skipped": skipped_count,
            "ids": processed_ids,
            "message": f"Uploaded {len(processed_ids)} photos, skipped {skipped_count} duplicates."
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[TimelineItem])
async def get_timeline(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return []

    try:
        # Fetch from Repo
        rows = photo_repo.get_timeline_photos(session_id)
        
        photos = []
        for r in rows:
            analysis_data = None
            if len(r) > 4 and r[4]:
                try:
                    analysis_data = json.loads(r[4])
                except:
                    pass

            analysis_date = None
            if len(r) > 5 and r[5]:
                analysis_date = r[5]

            photos.append(Photo(
                id=str(r[0]),
                filename=r[1],
                creation_date=r[2],
                uploaded_at=r[3],
                analysis=analysis_data,
                analysis_date=analysis_date
            ))
                
        # Grouping Logic: ALWAYS group by date (directory mode)
        timeline = []
        if not photos:
            return timeline

        current_group = []
        current_date = None

        for p in photos:
            if p.creation_date != current_date:
                # Flush previous group
                if current_group:
                    timeline.append(TimelineItem(
                        type="directory",
                        date=current_date,
                        items=current_group
                    ))
                # Start new group
                current_group = [p]
                current_date = p.creation_date
            else:
                current_group.append(p)
        
        # Flush last group
        if current_group:
            timeline.append(TimelineItem(
                type="directory",
                date=current_date,
                items=current_group
            ))
            
        logger.info(f"Timeline fetched: {len(timeline)} groups for session {session_id}")
        return timeline

    except Exception as e:
        logger.error(f"Timeline fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _append_group(timeline: List[TimelineItem], group: List[Photo], date_str: str):
    if len(group) == 1:
        # Single photo item
        timeline.append(TimelineItem(
            type="photo",
            date=date_str,
            data=group[0]
        ))
    else:
        # Virtual Directory
        timeline.append(TimelineItem(
            type="directory",
            date=date_str,
            items=group
        ))

@router.patch("/{photo_id}/date")
async def patch_photo_date(photo_id: str, request: Request, payload: dict):
    # payload: {"date": "2023-01-01"}
    session_id = request.cookies.get("session_id")
    new_date = payload.get("date")
    
    if not new_date:
        raise HTTPException(status_code=400, detail="Date required")

    try:
        photo_repo.update_date(photo_id, session_id, new_date)
        return {"status": "updated"}
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{photo_id}/content")
async def get_photo_content(photo_id: str, request: Request):
    session_id = request.cookies.get("session_id")
    try:
        result = photo_repo.get_photo_metadata(photo_id, session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        original_filename = result[0]
        stored_content = result[1]
        
        content = stored_content

        # Simple mimetype detection or default
        media_type = "image/jpeg" 
        if original_filename.lower().endswith(".png"):
            media_type = "image/png"
        
        return Response(content=content, media_type=media_type)
            
    except Exception as e:
        logger.error(f"Content fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{photo_id}/analyze", response_model=SinglePhotoAnalysisResponse)
async def analyze_photo(photo_id: str, request: Request, payload: SinglePhotoAnalysisRequest):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    try:
        # 1. Get Photo Content (Prioritize payload for local-only storage)
        if payload.base64_image:
            # Decode base64 image
            if "," in payload.base64_image:
                _, encoded = payload.base64_image.split(",", 1)
            else:
                encoded = payload.base64_image
            content = base64.b64decode(encoded)
        else:
            # Fallback to fetching from Repo (Database/Filesystem)
            result = photo_repo.get_photo_metadata(photo_id, session_id)
            if not result:
                raise HTTPException(status_code=404, detail="Photo not found")
            
            stored_content = result[1]
            content = stored_content

        # 2. Run Inference
        custom_labels = payload.candidate_labels
        
        execution_times = {}

        # Determine Preprocessing Strategy and prepare image
        start_time = time.perf_counter()
        prep_strategy = image_preprocess_service.recommend_prep_strategy(content)
        prepared_base64 = image_preprocess_service.prepare_image_base64(content)
        execution_times["image_preprocess"] = f"{(time.perf_counter() - start_time):.3f}s"
        
        primary_results = []
        primary_name = None

        # Run Primary (MedSigLIP)
        interpretation = None
        try:
            start_time = time.perf_counter()
            primary_results = medsiglip_wrapped_service.analyze_image(content, custom_labels=custom_labels)
            execution_times["primary_medsiglip"] = f"{(time.perf_counter() - start_time):.3f}s"
            primary_name = medsiglip_wrapped_service.service.model_name
            
            # Interpret results with configurable threshold
            interpretation = result_interpreter.interpret(
                primary_results, 
                margin_threshold=payload.margin_threshold
            )
        except Exception as e:
            logger.error(f"Primary inference failed: {e}")
            raise HTTPException(status_code=500, detail="Primary model failed")

        if primary_results:
            logger.info(f"Primary ({primary_name}) top result: {primary_results[0]['label']} ({primary_results[0]['score']:.2f})")
             
        results_dict = {
             "primary": primary_results,
             "interpretation": interpretation,
             "primary_model_name": primary_name,
             "preprocess_strategy": prep_strategy,
             "prepared_image_base64": prepared_base64,
             "execution_times": execution_times
        }
        
        # Merge with existing cache 
        try:
            current_cache = photo_repo.get_analysis_results(photo_id, session_id)
            if current_cache:
                start_data = json.loads(current_cache[0])
                if isinstance(start_data, dict):
                    if not primary_results and "primary" in start_data:
                        results_dict["primary"] = start_data["primary"]
                        results_dict["primary_model_name"] = start_data.get("primary_model_name")
        except:
            pass

        # Save results
        if not payload.base64_image:
            try:
                photo_repo.save_analysis_results(photo_id, session_id, json.dumps(results_dict))
            except Exception as e:
                logger.error(f"Failed to save analysis results: {e}")
        
        return SinglePhotoAnalysisResponse(
            photo_id=photo_id,
            predictions=results_dict.get("primary") or [],
            interpretation=results_dict.get("interpretation"),
            primary_model_name=results_dict.get("primary_model_name"),
            analysis_date=datetime.now().isoformat(),
            prepared_image_base64=results_dict.get("prepared_image_base64"),
            preprocess_strategy=results_dict.get("preprocess_strategy"),
            execution_times=results_dict.get("execution_times")
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{photo_id}")
async def delete_photo(photo_id: str, request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    try:
        photo_repo.delete_photo(photo_id, session_id)
        # Ideally delete file too, but keeping it simple for now
        return {"status": "deleted", "id": photo_id}
            
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from app.services.gradcam_service import gradcam_service

@router.post("/{photo_id}/saliency", response_model=SaliencyResponse)
async def generate_saliency_map(
    photo_id: str,
    payload: SaliencyRequest,
    request: Request
):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    try:
        # Decode base64 image
        if "," in payload.base64_image:
            _, encoded = payload.base64_image.split(",", 1)
        else:
            encoded = payload.base64_image
        content = base64.b64decode(encoded)
        
        # Generate Saliency (Grad-CAM)
        heatmap_bytes = gradcam_service.get_heatmap(content, payload.target_label)
        saliency_base64 = base64.b64encode(heatmap_bytes).decode('utf-8')
        
        return SaliencyResponse(
            photo_id=photo_id,
            saliency_base64=saliency_base64
        )
            
    except Exception as e:
        logger.error(f"Saliency generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("")
async def clear_session_photos(request: Request):
    """Deletes all photos associated with the current session ID."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    try:
        photo_repo.clear_session(session_id)
        
            
        return {"status": "cleared", "message": "All session photos deleted"}
            
    except Exception as e:
        logger.error(f"Clear session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
