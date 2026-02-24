import pytest
from unittest.mock import patch
from app.dal.photo_repo import photo_repo

@patch("app.routers.photos.image_preprocess_service")
def test_session_cleanup_flow(mock_prep, client):
    """
    Test the full lifecycle:
    1. Upload image
    2. Analyze image (mocked) and verify persistence
    3. Clear session
    4. Verify data and images are gone
    """
    mock_prep.recommend_prep_strategy.return_value = {"strategy": "crop", "reason": "mocked"}
    mock_prep.prepare_image_bytes.return_value = b"mocked-prepared-bytes"
    mock_prep.prepare_image_base64.return_value = "mocked-base64"
    
    session_id = "test-cleanup-session-001"
    client.cookies.set("session_id", session_id)

    # 1. Add Image
    img_content = b"fake-image-content-for-test"
    files = {"files": ("test_cleanup.jpg", img_content, "image/jpeg")}
    
    resp = client.post("/api/photos/upload", files=files)
    assert resp.status_code == 200
    
    # Verify it exists in timeline
    resp = client.get("/api/photos")
    assert resp.status_code == 200
    timeline = resp.json()
    
    # Find the photo
    photos = []
    for item in timeline:
        if item["type"] == "photo": photos.append(item["data"])
        elif item["type"] == "directory": photos.extend(item["items"])
    
    assert len(photos) >= 1
    # Filter for our specific file in case DB is shared
    my_photo = next((p for p in photos if p["filename"] == "test_cleanup.jpg"), None)
    assert my_photo is not None
    photo_id = my_photo["id"]

    # Verify via Repo directly
    meta = photo_repo.get_photo_metadata(photo_id, session_id)
    assert meta is not None
    assert meta[0] == "test_cleanup.jpg"

    # 2. Mock Analysis & Verify Persistence
    with patch("app.services.medsiglip_service.medsiglip_service.get_embeddings") as mock_embed:
        mock_embed.return_value = [{"label": "TestCondition", "score": 0.95}]
        
        # Call analyze
        resp = client.post(f"/api/photos/{photo_id}/analyze", json={})
        assert resp.status_code == 200
        
        # Check Response
        data = resp.json()
        assert data["predictions"][0]["label"] == "TestCondition"
        assert "analysis_date" in data
        
        # Check DB Persistence
        cached = photo_repo.get_analysis_results(photo_id, session_id)
        assert cached is not None
        assert "TestCondition" in cached[0]
        assert cached[1] is not None # Date exists

    # 3. Delete Session (Reset)
    resp = client.delete("/api/photos")
    assert resp.status_code == 200

    # 4. Verify Cleanup
    # Check Repo - Row should be gone
    meta = photo_repo.get_photo_metadata(photo_id, session_id)
    assert meta is None
    
    # Check Analysis - Should be gone
    cached = photo_repo.get_analysis_results(photo_id, session_id)
    assert cached is None
    
    # Check Timeline - Should be empty for this session
    resp = client.get("/api/photos")
    timeline = resp.json()
    assert len(timeline) == 0
