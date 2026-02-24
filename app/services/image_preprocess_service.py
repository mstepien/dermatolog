import logging
import functools
import time
import numpy as np
from PIL import Image
import io
from app.services.yolo_service import yolo_service

logger = logging.getLogger(__name__)

from enum import Enum

class PreprocessStrategy(str, Enum):
    CROP = "crop"
    PAD = "pad"
    NONE = "none"

class ImagePreprocessService:
    def __init__(self):
        pass


    def get_lesion_bbox(self, image_content: bytes, threshold: float = 0.25) -> tuple:
        """
        Detects the lesion bounding box using YOLOv8-Nano.
        """
        try:
            with Image.open(io.BytesIO(image_content)) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                width, height = img.size
                
                model = yolo_service.load_model()
                if model is None:
                    return (0, 0, width, height)
                    
                # Run inference
                results = model.predict(img, conf=threshold, verbose=False)
                
                if not results or len(results[0].boxes) == 0:
                    logger.debug("YOLO detection found no boxes, falling back to full image")
                    return (0, 0, width, height)
                    
                # Take the highest confidence box (YOLO sorts by confidence by default)
                box = results[0].boxes[0].xyxy[0].cpu().numpy()
                return (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
        except Exception as e:
            logger.error(f"YOLO detection failed: {e}")
            return None


    @functools.lru_cache(maxsize=32)
    def recommend_prep_strategy(self, image_bytes: bytes) -> dict:
        """
        Decides whether to 'crop' or 'pad' based on object detection.
        """
        start_time = time.perf_counter()
        image = Image.open(io.BytesIO(image_bytes))
        width, height = image.size
        
        if width == height:
            return {
                "strategy": PreprocessStrategy.NONE, 
                "reason": "Already square",
                "execution_time": f"{(time.perf_counter() - start_time):.3f}s"
            }

        if width <= 448 and height <= 448:
            return {
                "strategy": PreprocessStrategy.PAD, 
                "reason": "Image is 448x448 or smaller; padding to square to avoid any data loss or scale-down",
                "execution_time": f"{(time.perf_counter() - start_time):.3f}s"
            }

        bbox = self.get_lesion_bbox(image_bytes)
        if not bbox:
            return {
                "strategy": PreprocessStrategy.CROP, 
                "reason": "Detection failed, defaulting to center crop",
                "execution_time": f"{(time.perf_counter() - start_time):.3f}s"
            }

        x1, y1, x2, y2 = bbox
        
        # Center square boundaries
        new_dim = min(width, height)
        if width > height:
            # Landscape
            crop_x1 = (width - new_dim) / 2
            crop_x2 = (width + new_dim) / 2
            
            # Check if bbox is outside the horizontal center crop
            is_cut = (x1 < crop_x1) or (x2 > crop_x2)
        else:
            # Portrait
            crop_y1 = (height - new_dim) / 2
            crop_y2 = (height + new_dim) / 2
            
            # Check if bbox is outside the vertical center crop
            is_cut = (y1 < crop_y1) or (y2 > crop_y2)

        if is_cut:
            return {
                "strategy": PreprocessStrategy.PAD, 
                "reason": "Object extends beyond center crop area",
                "bbox": bbox,
                "execution_time": f"{(time.perf_counter() - start_time):.3f}s"
            }
        else:
            return {
                "strategy": PreprocessStrategy.CROP, 
                "reason": "Object fully contained in center crop area",
                "bbox": bbox,
                "execution_time": f"{(time.perf_counter() - start_time):.3f}s"
            }

    def prepare_image(self, image: Image.Image, target_size: tuple = (448, 448)) -> Image.Image:
        """
        Intelligently prepares an image by either cropping or padding to a square,
        then resizing to target_size.
        """
        # Convert to bytes for strategy detection
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        image_bytes = img_byte_arr.getvalue()
        
        strategy_res = self.recommend_prep_strategy(image_bytes)
        strategy = strategy_res["strategy"]
        
        width, height = image.size
        
        if strategy == PreprocessStrategy.CROP or strategy == PreprocessStrategy.NONE:
            # Traditional center crop (or already square)
            new_dim = min(width, height)
            left = (width - new_dim) / 2
            top = (height - new_dim) / 2
            right = (width + new_dim) / 2
            bottom = (height + new_dim) / 2
            image = image.crop((left, top, right, bottom))
        elif strategy == PreprocessStrategy.PAD:
            # Pad to square
            new_dim = max(width, height)
            # Use black background for padding as it is common for clinical vision models
            new_image = Image.new("RGB", (new_dim, new_dim), (0, 0, 0)) 
            if width > height:
                # Landscape -> Pad Top/Bottom
                new_image.paste(image, (0, (new_dim - height) // 2))
            else:
                # Portrait -> Pad Left/Right
                new_image.paste(image, ((new_dim - width) // 2, 0))
            image = new_image
        
        # Finally resize
        if image.size != target_size:
            logger.debug(f"Resizing image to {target_size}")
            image = image.resize(target_size, Image.Resampling.LANCZOS)
            
        return image

    def prepare_image_base64(self, image_bytes: bytes, target_size: tuple = (448, 448)) -> str:
        """
        Prepares image and returns as base64 data URI for UI debugging/display.
        """
        import base64
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            prepared_image = self.prepare_image(image, target_size)
            
            buf = io.BytesIO()
            prepared_image.save(buf, format="JPEG")
            img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{img_b64}"
        except Exception as e:
            logger.error(f"Failed to prepare image base64: {e}")
            return None

    def prepare_image_bytes(self, image_bytes: bytes, target_size: tuple = (448, 448)) -> bytes:
        """
        Helper to prepare image directly from bytes and return bytes.
        """
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            prepared_image = self.prepare_image(image, target_size)
            
            buf = io.BytesIO()
            prepared_image.save(buf, format="JPEG")
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Failed to prepare image bytes: {e}")
            raise e

image_preprocess_service = ImagePreprocessService()
