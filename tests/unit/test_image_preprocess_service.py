import unittest
from unittest.mock import MagicMock, patch
import os
import io
from PIL import Image
import numpy as np
from app.services.image_preprocess_service import image_preprocess_service, PreprocessStrategy

class TestImagePreprocessService(unittest.TestCase):
    def setUp(self):
        self.image_path = "tests/data/Melanoma1280x891.jpg"
        self.small_image_path = "tests/data/Melanoma400x278.jpg"
        self.melanoma_path = "tests/data/melanoma.jpg"
        self.mole_path = "tests/data/mole.jpg"
        
        # Verify all files exist
        for p in [self.image_path, self.small_image_path, self.melanoma_path, self.mole_path]:
            if not os.path.exists(p):
                print(f"DEBUG: Missing test file {p}")
                # We skip instead of failing to avoid breaking CI if files are partially missing
                # though they should be in the repo.
                self.skipTest(f"Missing required test data: {p}")
            
        image_preprocess_service.recommend_prep_strategy.cache_clear()

    def test_melanoma_crop_vs_pad_logic(self):
        """
        Test the logic that decides between cropping and padding based on detection.
        Using Melanoma1280×891.jpg (Landscape: 1280x891).
        Center crop window would be [194.5, 0, 1085.5, 891].
        """
        with open(self.image_path, "rb") as f:
            content = f.read()
        
        # Verify image dimensions first
        img = Image.open(io.BytesIO(content))
        self.assertEqual(img.size, (1280, 891))

        # Case 1: Lesion is centered -> Strategy: CROP
        with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(500, 300, 700, 500)):
            image_preprocess_service.recommend_prep_strategy.cache_clear()
            res = image_preprocess_service.recommend_prep_strategy(content)
            self.assertEqual(res["strategy"], PreprocessStrategy.CROP)
            self.assertIn("fully contained", res["reason"])

        # Case 2: Lesion is at the far left edge (x=50) -> Strategy: PAD
        with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(50, 300, 200, 500)):
            image_preprocess_service.recommend_prep_strategy.cache_clear()
            res = image_preprocess_service.recommend_prep_strategy(content)
            self.assertEqual(res["strategy"], PreprocessStrategy.PAD)
            self.assertIn("extends beyond", res["reason"])

        # Case 3: Lesion is at the far right edge (x=1200) -> Strategy: PAD
        with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(1100, 300, 1250, 500)):
            image_preprocess_service.recommend_prep_strategy.cache_clear()
            res = image_preprocess_service.recommend_prep_strategy(content)
            self.assertEqual(res["strategy"], PreprocessStrategy.PAD)
            self.assertIn("extends beyond", res["reason"])

    def test_melanoma_real_image_strategy(self):
        """
        Test that the real Melanoma1280×891.jpg results in PAD strategy.
        This image has the melanoma near the edge, so cropping would cut it.
        We mock the detection bbox to represent this edge-positioning.
        """
        with open(self.image_path, "rb") as f:
            content = f.read()
            
        # Mocking the detection result for this specific file:
        # For a 1280 wide image, center crop starts at 194.5.
        # We mock a lesion at the far left edge (x=50) to verify PAD logic.
        with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(50, 400, 250, 600)):
            image_preprocess_service.recommend_prep_strategy.cache_clear()
            res = image_preprocess_service.recommend_prep_strategy(content)
            
            self.assertEqual(res["strategy"], PreprocessStrategy.PAD)
            self.assertIn("extends beyond", res["reason"])

    def test_mole_crop_vs_pad_strategy(self):
        """
        Test logic for mole.jpg (670x442).
        Center crop x-range is [114, 556].
        """
        path = "tests/data/mole.jpg"
        if not os.path.exists(path):
            self.skipTest("mole.jpg not found")

        with open(path, "rb") as f:
            content = f.read()
        
        # Case 1: Centered mole -> CROP
        with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(200, 100, 400, 300)):
            image_preprocess_service.recommend_prep_strategy.cache_clear()
            res = image_preprocess_service.recommend_prep_strategy(content)
            self.assertEqual(res["strategy"], PreprocessStrategy.CROP)

        # Case 2: Mole at left edge (x=50) -> PAD (Cutoff is at x=114)
        with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(50, 100, 150, 300)):
            image_preprocess_service.recommend_prep_strategy.cache_clear()
            res = image_preprocess_service.recommend_prep_strategy(content)
            self.assertEqual(res["strategy"], PreprocessStrategy.PAD)

    def test_prepare_image_basic(self):
        """Test basic crop/resize via prepare_image."""
        # Force a crop strategy by mocking get_lesion_bbox to return centered result
        # Use existing melanoma.jpg (224x224)
        with Image.open(self.melanoma_path) as img:
            with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(90, 90, 130, 130)):
                image_preprocess_service.recommend_prep_strategy.cache_clear()
                prepared = image_preprocess_service.prepare_image(img, (50, 50))
                self.assertEqual(prepared.size, (50, 50))

    def test_prepare_image_pad(self):
        """Test padding via prepare_image."""
        # Force a pad strategy by using a LARGE image that exceeds 448x448
        # Use existing Melanoma1280x891.jpg
        with Image.open(self.image_path) as img:
            # Mock lesion at the very left (x=50) so it's outside center crop
            with patch.object(image_preprocess_service, 'get_lesion_bbox', return_value=(50, 200, 150, 300)):
                image_preprocess_service.recommend_prep_strategy.cache_clear()
                prepared = image_preprocess_service.prepare_image(img, (50, 50))
                self.assertEqual(prepared.size, (50, 50))
                # Resize to 50x50 -> should have black bars if PAD was used
                pixels = list(prepared.getdata())
                top_pixel = pixels[0] 
                self.assertEqual(top_pixel, (0, 0, 0)) # Should be black padding

    def test_small_image_bypass_logic(self):
        """Test that images <= 448x448 return PAD strategy to avoid cropping/scaling down."""
        # Use Melanoma400x278.jpg as the small rectangular image
        with open(self.small_image_path, "rb") as f:
            content = f.read()
        
        image_preprocess_service.recommend_prep_strategy.cache_clear()
        res = image_preprocess_service.recommend_prep_strategy(content)
        
        self.assertEqual(res["strategy"], PreprocessStrategy.PAD)
        self.assertIn("padding to square to avoid any data loss", res["reason"])

    def test_melanoma_small_padding_real_flow(self):
        """
        Test that Melanoma400x278.jpg is padded to 400x400.
        It should not be scaled down (kept at 400 max dim).
        """
        with open(self.small_image_path, "rb") as f:
            content = f.read()
            
        # 1. Check recommendation
        res = image_preprocess_service.recommend_prep_strategy(content)
        self.assertEqual(res["strategy"], PreprocessStrategy.PAD)
        
        # 2. Check preparation result
        # We specify target_size=(400, 400) to verify it stays at that size
        img = Image.open(io.BytesIO(content))
        prepared = image_preprocess_service.prepare_image(img, target_size=(400, 400))
        
        self.assertEqual(prepared.size, (400, 400))
        
        # Verify symmetric padding (top and bottom should be black)
        # 400x278 -> 400x400 square. Padding = (400-278)/2 = 61 pixels top and bottom
        pixels = list(prepared.getdata())
        
        # Top-left pixel should be black padding (0,0,0)
        self.assertEqual(pixels[0], (0, 0, 0))
        # Top-middle pixel should be black padding
        self.assertEqual(pixels[200], (0, 0, 0))
        
        # Center pixel (200, 200) should be the original image content (not black)
        center_pixel = pixels[200 * 400 + 200]
        self.assertNotEqual(center_pixel, (0, 0, 0))

if __name__ == '__main__':
    unittest.main()
