from pydantic import BaseModel
from typing import List, Optional
class HealthCheckResponse(BaseModel):
    status: str
    yolo_available: bool

class Photo(BaseModel):
    id: str
    filename: str
    creation_date: str  # ISO date string YYYY-MM-DD
    uploaded_at: str
    analysis: Optional[object] = None # Can be List[dict] (legacy) or dict (new with comparison)
    analysis_date: Optional[str] = None
    local_content: Optional[str] = None # Base64 data for client-side storage


# Response model for the timeline: a list of either Photo (single) or VirtualDirectory (group)
# In Pydantic V2 we might use Union, but for simplicity/JSON serialization,
# we can return a list of objects that have a 'type' field.

class TimelineItem(BaseModel):
    type: str # 'photo' or 'directory'
    date: str
    data: Optional[Photo] = None # If type is photo
    items: Optional[List[Photo]] = None # If type is directory



from app.config import INTERPRETER_MARGIN_THRESHOLD

class SinglePhotoAnalysisRequest(BaseModel):
    # Default labels for zero-shot classification from centralized config
    candidate_labels: Optional[List[str]] = None
    model: Optional[str] = "medsiglip" # "medsiglip" only now
    base64_image: Optional[str] = None # Client-side image data
    margin_threshold: Optional[float] = INTERPRETER_MARGIN_THRESHOLD

class SinglePhotoAnalysisResponse(BaseModel):
    photo_id: str
    predictions: List[dict]
    primary_model_name: Optional[str] = None
    analysis_date: Optional[str] = None
    prepared_image_base64: Optional[str] = None
    saliency_base64: Optional[str] = None # Returning saliency as base64
    interpretation: Optional[dict] = None
    preprocess_strategy: Optional[dict] = None
    execution_times: Optional[dict] = None

class SaliencyRequest(BaseModel):
    base64_image: str
    target_label: str

class SaliencyResponse(BaseModel):
    photo_id: str
    saliency_base64: str
