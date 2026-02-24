import os
import time
import pytest
from PIL import Image

@pytest.fixture(scope="function")
def dummy_image():
    """Creates a temporary dummy image for testing and cleans it up after."""
    filename = "test_e2e_img.jpg"
    img = Image.new('RGB', (100, 100), color='green')
    img.save(filename)
    yield filename
    if os.path.exists(filename):
        os.remove(filename)

def test_duplicate_upload_shows_warning_context(page, dummy_image, test_server):
    """
    Test flow:
    1. Clear session to start fresh.
    2. Upload an image.
    3. Upload the SAME image again.
    4. Verify 'Upload Notice' appears.
    5. Verify NO error alerts appear.
    """
    # 1. Clear Session (Navigate and click Clear if exists)
    page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
    page.goto(test_server)
    
    # Check if we need to clear previous state
    # We use a locator for the button
    clear_btn = page.locator("sl-button", has_text="Clear All").first
    
    # Wait briefly to see if it appears (it depends on timeline length)
    try:
        clear_btn.wait_for(state="visible", timeout=2000)
        page.once("dialog", lambda dialog: dialog.accept())
        clear_btn.click()
        # Wait for timeline to empty
        page.locator("text=No photos yet").wait_for(state="visible", timeout=5000)
        page.reload()
    except:
        pass # Button not found, session likely empty

    # 2. Upload First Image
    print("Uploading first image...")
    page.set_input_files("input[type='file']", dummy_image)
    
    # Wait for image to appear in DOM with data: URI
    try:
        page.locator("img[src^='data:image/']").first.wait_for(state="visible", timeout=30000)
    except Exception as e:
        print(f"Timeline items found: {page.locator('.timeline-item').count()}")
        print(f"Page content dump: {page.content()}")
        raise e

    # 3. Upload Duplicate Image
    # We need to trigger the change event again.
    # To ensure the 'change' event fires even if we select the exact same file path,
    # we first clear the input.
    page.set_input_files("input[type='file']", [])
    
    # Now set the same file again
    page.set_input_files("input[type='file']", dummy_image)

    # 4. Verify Warning Toast
    # We look for an alert with variant='warning'
    warning_alert = page.locator("sl-alert[variant='warning']")
    warning_alert.wait_for(state="visible", timeout=20000)
    
    content = warning_alert.text_content()
    assert "Upload Notice" in content
    assert "Skipped" in content

    # 5. Verify NO Error Toast
    # variant='danger' is used for errors
    error_alert = page.locator("sl-alert[variant='danger']")
    
    # Wait a bit to ensure no error pops up
    page.wait_for_timeout(1000) 
    
    assert not error_alert.is_visible(), f"Found unexpected error alert: {error_alert.text_content() if error_alert.is_visible() else ''}"
