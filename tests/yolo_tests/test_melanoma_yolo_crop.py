
import pytest
import io
import os
from PIL import Image
from app.services.image_preprocess_service import image_preprocess_service, PreprocessStrategy

from unittest.mock import MagicMock, patch

def test_melanoma_wiki_a_crop_strategy():
    """
    Test that melanoma_wiki_A.jpg (centered/rectangular) results in a CROP strategy.
    We mock the YOLO output to simulate a centered lesion detection.
    """
    image_path = "tests/data/melanoma_wiki_A.jpg"
    
    # Ensure image exists
    assert os.path.exists(image_path), f"Test image missing: {image_path}"
        
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size

    # Simulate a centered lesion (roughly in the middle of the image)
    # BBox format is [x1, y1, x2, y2]
    mock_bbox = [w*0.3, h*0.3, w*0.7, h*0.7]
    
    # Create mock YOLO results object
    mock_results = MagicMock()
    mock_box = MagicMock()
    mock_box.xyxy = [MagicMock()]
    mock_box.xyxy[0].cpu().numpy.return_value = mock_bbox
    mock_results.boxes = [mock_box]

    # Patch yolo_service to return our mock
    with patch("app.services.image_preprocess_service.yolo_service.load_model") as mock_load:
        mock_model = MagicMock()
        mock_model.predict.return_value = [mock_results]
        mock_load.return_value = mock_model
        
        # Clear cache to ensure fresh run
        image_preprocess_service.recommend_prep_strategy.cache_clear()
        
        # Run recommendation
        result = image_preprocess_service.recommend_prep_strategy(image_bytes)
    
        # Assert CROP strategy
        assert result['strategy'] == PreprocessStrategy.CROP, \
            f"Expected CROP for centered lesion in {image_path}, but got {result['strategy']}. Reason: {result.get('reason')}"
        
        print(f"\n✅ SUCCESS: Preprocessing correctly chose CROP for {image_path}")
        print(f"Reason: {result.get('reason')}")
        print(f"Simulated BBox: {result.get('bbox')}")
