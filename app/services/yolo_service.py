import logging
import os

logger = logging.getLogger(__name__)

class YOLOService:
    def __init__(self):
        self.model = None

    def load_model(self):
        if self.model is None:
            try:
                from ultralytics import YOLO
                # Use YOLOv8-Nano
                logger.info("Loading YOLOv8-Nano model...")
                self.model = YOLO('yolov8n.pt')
            except ImportError:
                logger.warning("ultralytics not installed. YOLO detection will be skipped.")
                return None
        return self.model

yolo_service = YOLOService()
