
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.medsiglip_service import medsiglip_service
from PIL import Image
import io

# We need to ensure we can run this test even if we are not in a full app context,
# but the service relies on having torch/transformers installed.

# We need to ensure we can run this test even if we are not in a full app context,
# but the service relies on having torch/transformers installed.

def test_medsiglip_inference_on_melanoma():
    """
    Test MedSigLIP inference on a melanoma image.
    This test verifies that the model loads and runs prediction.
    """
    image_path = "tests/data/melanoma.jpg"
    
    # Ensure image exists (created by create_test_image.py)
    if not os.path.exists(image_path):
        pytest.skip("Melanoma test image not found. Run create_test_image.py first.")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Define candidate labels
    labels = ["Melanoma", "Nevus", "Healthy Skin"]

    # Use MedSigLIP model for testing.
    from app.services.medsiglip_service import MedSigLIPService
    test_service = MedSigLIPService(model_name="google/medsiglip-448")
    
    # Run inference
    # Ensure no fallback occurred
    assert test_service.model_name == "google/medsiglip-448", "Test failing: Falling back to public model. Check HF_TOKEN."

    # Note: The first run might take time to download the model
    try:
        results = test_service.get_embeddings(image_bytes, texts=labels)
        
        print("\nInference Results:")
        for res in results:
            print(f"  {res['label']}: {res['score']:.4f}")

        # Basic assertions
        assert isinstance(results, list)
        assert len(results) == len(labels)
        assert "label" in results[0]
        assert "score" in results[0]
        
        # Verify scores sum to roughly 1 (softmax)
        total_score = sum(r["score"] for r in results)
        assert abs(total_score - 1.0) < 0.05

        # Since we use a dummy image, we can't assert it's classified as Melanoma effectively,
        # but we can assert the *structure* of the response is correct.
        
    except Exception as e:
        pytest.fail(f"Inference failed with error: {e}")
