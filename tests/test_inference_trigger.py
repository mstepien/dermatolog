
import os
import pytest
from PIL import Image

@pytest.fixture(scope="function")
def dummy_image():
    """Creates a temporary dummy image for testing."""
    filename = "test_trigger.jpg"
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(filename)
    yield filename
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except:
            pass

def test_inference_starts_on_upload(page, dummy_image, test_server):
    """
    Verifies that after selecting a file, the /analyze endpoint is called.
    """
    page.goto(test_server)
    
    # Clear session to ensure we are fresh
    clear_btn = page.locator("sl-button", has_text="Clear All").first
    if clear_btn.is_visible():
        page.once("dialog", lambda dialog: dialog.accept())
        clear_btn.click()
        page.locator("text=No photos yet").wait_for(state="visible", timeout=5000)

    # We expect a POST to /api/photos/*/analyze
    # The app.js calls it after a 300ms timeout
    print("Uploading file and waiting for analyze request...")
    with page.expect_response("**/api/photos/*/analyze", timeout=60000) as response_info:
        page.set_input_files("input[type='file']", dummy_image)
        
    response = response_info.value
    print(f"Intercepted analyze request: {response.url}")
    assert response.request.method == "POST", "Expected a POST request for analysis"
    assert response.ok, f"Analyze request failed with status {response.status}"
    
    # Also verify UI shows it's analyzing
    photo_item = page.locator("[data-analyzed='false']").first
    # It might be very fast, but usually it stays 'Pending' or shows a spinner
    # If it's already done, it should have [data-analyzed='true']
    
    page.wait_for_selector("[data-analyzed='true']", timeout=300000)
    print("Inference completed successfully according to DOM state.")
