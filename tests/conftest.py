import os
import sys
import time
import subprocess
import requests
import socket
from contextlib import closing

# Ensure project root is in path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

import pytest
from fastapi.testclient import TestClient
from app.main import app

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

@pytest.fixture
def client():
    """
    Test client for the FastAPI app.
    """
    return TestClient(app)

@pytest.fixture(scope="session")
def test_server():
    """
    Starts a uvicorn server in a subprocess for E2E tests.
    Yields the base URL (e.g., http://127.0.0.1:8001).
    """
    port = find_free_port()
    host = "127.0.0.1"
    base_url = f"http://{host}:{port}"
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT_ROOT # Ensure standard imports work
    
    log_path = f"/tmp/test_server_{port}.log"
    log_file = open(log_path, "w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", host, "--port", str(port)],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=PROJECT_ROOT # Start from project root
    )

    # Health check loop
    start_time = time.time()
    while time.time() - start_time < 10:
        try:
            resp = requests.get(f"{base_url}/api/health")
            if resp.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(0.1)
    else:
        # Timeout
        print(f"Server failed to start. Logs in {log_path}")
        proc.kill()
        log_file.close()
        raise RuntimeError("Test server failed to start")

    yield base_url

    # Teardown
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
    
    log_file.close()
    
    # Read and print logs if failed (or always for debugging now)
    try:
        with open(log_path, "r") as f:
            print(f"\n--- TEST SERVER LOGS ({port}) ---\n")
            print(f.read())
            print(f"\n--- END LOGS ---\n")
    except:
        pass
    
    # Clean up log file


    # Clean up log file
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
        except:
            pass
