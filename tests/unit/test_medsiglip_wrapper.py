import pytest
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.medsiglip_modality_wrapper import ClinicalModalityWrapper
from app.services.medsiglip_service import MedSigLIPService

def test_medsiglip_wrapper_templating():
    """
    Test that the wrapper correctly templates and maps labels.
    """
    image_path = "tests/data/melanoma.jpg"
    if not os.path.exists(image_path):
        pytest.skip("Melanoma test image not found.")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Use a real service if possible, or mock it. 
    # For now, we'll try to use the real one if HF_TOKEN is present.
    if not os.environ.get("HF_TOKEN"):
        pytest.skip("HF_TOKEN missing, cannot run MedSigLIP tests.")

    service = MedSigLIPService()
    wrapper = ClinicalModalityWrapper(service=service, modality="macroscopic")

    # Test with custom labels
    custom_labels = ["Melanoma", "Normal Skin"]
    results = wrapper.analyze_image(image_bytes, custom_labels=custom_labels)

    assert len(results) == len(custom_labels)
    # Check that labels are mapped back to short names
    labels_received = [r["label"] for r in results]
    assert "Melanoma" in labels_received
    assert "Normal Skin" in labels_received
    
    # Check that descriptions (prompts) were used
    assert "A patient-submitted smartphone photograph showing" in results[0]["description"]

def test_medsiglip_wrapper_default_labels():
    """
    Test that the wrapper works with default clinical labels.
    """
    image_path = "tests/data/melanoma.jpg"
    if not os.path.exists(image_path):
        pytest.skip("Melanoma test image not found.")

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    if not os.environ.get("HF_TOKEN"):
        pytest.skip("HF_TOKEN missing, cannot run MedSigLIP tests.")

    service = MedSigLIPService()
    wrapper = ClinicalModalityWrapper(service=service, modality="dermoscopy")
    
    # Run subset for speed if we were mocking, but here we run full inference
    # Just check return structure
    results = wrapper.analyze_image(image_bytes)
    
    assert len(results) == 12 # Matches MEDSIGLIP_DERMATOLOGY_NARROW_LABELS
    assert "Dermoscopy image revealing" in results[0]["description"]
    assert "score" in results[0]
