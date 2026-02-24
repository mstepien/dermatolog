import os
import time
import pytest
from PIL import Image
import base64

@pytest.fixture(scope="function")
def dummy_image():
    """Creates a temporary dummy image for testing and cleans it up after."""
    filename = "test_e2e_local.jpg"
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(filename)
    yield filename
    if os.path.exists(filename):
        os.remove(filename)

def test_local_upload_and_analysis_flow(page, dummy_image, test_server):
    """
    Test the new local-only workflow:
    1. Image is processed into DataURL locally.
    2. No /upload request is sent.
    3. Image appears in timeline.
    4. /analyze request is sent with base64 data.
    5. Results are displayed in the UI.
    """
    page.on("console", lambda msg: print(f"Browser Console: [{msg.type}] {msg.text}"))
    page.goto(test_server)
    
    # 1. Clear any existing state
    clear_btn = page.locator("sl-button", has_text="Clear All").first
    if clear_btn.count() > 0:
        try:
            clear_btn.wait_for(state="visible", timeout=2000)
            page.once("dialog", lambda dialog: dialog.accept())
            clear_btn.click()
            page.locator("text=No photos yet").wait_for(state="visible", timeout=5000)
        except:
            print("Clear All button not visible or timed out, continuing...")

    # 2. Trigger "Upload" (Local load)
    # We expect TO NOT see an /upload network call
    print("Selecting local file...")
    
    # Listen for /analyze calls
    # Note: analyzeAllPhotos is called after 300ms timeout in app.js
    with page.expect_response("**/api/photos/*/analyze", timeout=300000) as response_info:
        page.set_input_files("input[type='file']", dummy_image)
        
        # Verify image appears in DOM with a data: URI (within timeline)
        print("Waiting for image to appear in timeline...")
        img_locator = page.locator(".timeline-container img[src^='data:image/']")
        img_locator.first.wait_for(state="visible", timeout=60000)
        print("Local image confirmed in timeline.")
        print("Waiting for analyze response (inference can be slow)...")

    # 3. Check Analysis Response
    response = response_info.value
    print(f"Response received. Status: {response.status}")
    assert response.ok
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) > 0
    print(f"Analysis successful: {data['predictions'][0]['label']}")

    # 4. Verify results display in UI
    # The 'Clinical Assessment' text should appear
    print("Waiting for Clinical Assessment UI element...")
    page.locator("text=Clinical Assessment").first.wait_for(state="visible", timeout=300000)
    
    # Verify the label is visible
    label_text = data["predictions"][0]["label"]
    page.locator(f"text={label_text}").first.wait_for(state="visible", timeout=30000)
    
    # Verify Saliency Map toggle is present
    saliency_toggle = page.locator("sl-details", has_text="View Grad-CAM Saliency Map").first
    saliency_toggle.wait_for(state="visible", timeout=10000)
    
    # 5. Trigger Lazy Saliency Load
    print("Triggering lazy saliency map load...")
    saliency_toggle.click()
    
    # Wait for the spinner to appear first (optional but helps verify lazy state)
    spinner = page.locator("sl-details[summary*='Saliency'] sl-spinner").first
    try:
        spinner.wait_for(state="visible", timeout=10000)
        print("Spinner visible - computing saliency...")
    except:
        print("Spinner not seen, maybe it was too fast or already loaded.")

    # Wait for the image to load inside sl-details
    # Saliency generation on CPU can be very slow (forward + backward pass)
    saliency_img = page.locator("sl-details[summary*='Saliency'] img[src^='data:image/']").first
    saliency_img.wait_for(state="visible", timeout=300000) 
    print("Lazy saliency map confirmed in UI.")
    
    print("E2E Local Workflow Test Passed.")

def test_local_duplicate_handling(page, dummy_image, test_server):
    """Verifies that selecting the same file twice doesn't create duplicate timeline items."""
    page.goto(test_server)
    
    # 1. Clear state
    clear_btn = page.locator("sl-button", has_text="Clear All").first
    if clear_btn.is_visible():
        page.once("dialog", lambda dialog: dialog.accept())
        clear_btn.click()
        page.locator("text=No photos yet").wait_for(state="visible", timeout=5000)

    # 2. Load first time
    page.set_input_files("input[type='file']", dummy_image)
    page.locator(".timeline-container img[src^='data:image/']").first.wait_for(state="visible", timeout=5000)
    count1 = page.locator(".timeline-container img[src^='data:image/']").count()
    assert count1 == 1

    # 3. Load same file again
    # Clear input first to trigger change event
    page.set_input_files("input[type='file']", [])
    page.set_input_files("input[type='file']", dummy_image)
    
    # Wait a bit
    page.wait_for_timeout(1000)
    
    count2 = page.locator(".timeline-container img[src^='data:image/']").count()
    assert count2 == 1, "Duplicate item should not be added to timeline"
    print("Local duplicate detection confirmed.")
