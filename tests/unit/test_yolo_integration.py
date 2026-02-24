
import pytest
from unittest.mock import MagicMock, patch
import sys
from app.services.yolo_service import YOLOService

def test_yolo_load_model_success():
    """Test that YOLO model loads when ultralytics is present."""
    service = YOLOService()
    
    mock_yolo = MagicMock()
    with patch.dict(sys.modules, {'ultralytics': MagicMock()}):
        from ultralytics import YOLO
        with patch('ultralytics.YOLO', return_value=mock_yolo):
            model = service.load_model()
            assert model == mock_yolo
            assert service.model == mock_yolo

def test_yolo_load_model_missing_dependency():
    """Test that YOLO model returns None when ultralytics is missing."""
    service = YOLOService()
    
    with patch.dict(sys.modules, {'ultralytics': None}):
        # In newer python/pytest patching sys.modules to None might behave differently or raise differently
        # But our code catches ImportError specifically.
        with patch('builtins.__import__', side_effect=ImportError("No module named 'ultralytics'")):
            model = service.load_model()
            assert model is None
            assert service.model is None

def test_preprocess_graceful_fallback():
    """Test that ImagePreprocessService handles YOLO failure gracefully."""
    from app.services.image_preprocess_service import ImagePreprocessService
    from PIL import Image
    import io
    
    service = ImagePreprocessService()
    
    # Create a dummy image
    img = Image.new('RGB', (1000, 500), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    image_bytes = img_byte_arr.getvalue()

    # Mock get_lesion_bbox to return None (simulating YOLO failure)
    with patch.object(service, 'get_lesion_bbox', return_value=None):
        strategy = service.recommend_prep_strategy(image_bytes)
        assert strategy['strategy'] == "crop"
        assert "Detection failed" in strategy['reason']
