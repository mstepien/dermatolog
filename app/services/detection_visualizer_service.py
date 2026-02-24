import logging
from PIL import Image, ImageDraw
import io
import numpy as np

from app.services.yolo_service import yolo_service

logger = logging.getLogger(__name__)

class DetectionVisualizerService:
    def __init__(self):
        pass

    def get_detection_visual(self, image_content: bytes, target_label: str = None) -> bytes:
        """
        Detects lesions using YOLOv8-Nano and draws a bounding box.
        Returns the image with box as bytes (JPEG).
        """
        try:
            # Prepare Inputs
            image = Image.open(io.BytesIO(image_content)).convert("RGB")
            
            model = yolo_service.load_model()
            results = model.predict(image, conf=0.25, verbose=False)
            
            # Draw on image
            draw = ImageDraw.Draw(image)
            
            found = False
            if results and len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    b = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    
                    # Draw red box for lesion
                    draw.rectangle([b[0], b[1], b[2], b[3]], outline="red", width=5)
                    # Draw label background
                    label = f"Lesion {conf:.2f}"
                    draw.text((b[0] + 5, b[1] + 5), label, fill="red")
                    found = True
            
            if not found:
                # Optional: draw some indicator that nothing was found?
                # Or just return original image.
                pass

            # Return
            buf = io.BytesIO()
            image.save(buf, format="JPEG")
            return buf.getvalue()

        except Exception as e:
            logger.error(f"YOLO visualizer error: {e}")
            return image_content

detection_visualizer_service = DetectionVisualizerService()
