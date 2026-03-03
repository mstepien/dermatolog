import sys
import os

# Add the project root to the python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from app.main import app

def test_session_cookie_allows_cross_origin_iframe():
    """
    Test to check if the session_id cookie is configured to allow
    cross-origin iframe embedding and requests.
    This requires SameSite=None and Secure=True HTTP cookie attributes.
    """
    print("Running test_session_cookie_allows_cross_origin_iframe...", flush=True)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    
    # Get the Set-Cookie header
    set_cookie_header = response.headers.get("set-cookie")
    assert set_cookie_header is not None, "No Set-Cookie header found"
    print(f"Set-Cookie header found: {set_cookie_header}", flush=True)
    
    # We expect 'session_id=' to be part of the setup
    assert "session_id=" in set_cookie_header
    
    # For iframe cross-origin, we must have SameSite=None and Secure
    set_cookie_lower = set_cookie_header.lower()
    
    assert "samesite=none" in set_cookie_lower, "Cookie must have SameSite=None to work in an iframe"
    assert "secure" in set_cookie_lower, "Cookie must be marked Secure to use SameSite=None"
    print("Test passed!", flush=True)

if __name__ == "__main__":
    test_session_cookie_allows_cross_origin_iframe()
