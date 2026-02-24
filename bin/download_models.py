import os
import sys
from huggingface_hub import snapshot_download
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MODELS = [
    "google/medsiglip-448"
]

YOLO_MODELS = [
    "yolov8n.pt"
]

def check_and_download():
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("Warning: HF_TOKEN not found in environment. Gated models like MedSigLIP may fail to download.")
    
    success = True
    for model_id in MODELS:
        print(f"\n--- Checking {model_id} ---")
        try:
            # snackshot_download checks if files are already present and only downloads missing pieces
            path = snapshot_download(
                repo_id=model_id, 
                token=token,
                local_files_only=False # Set to True if we only wanted to check, but user wants to download too
            )
            print(f"Model {model_id} is ready at: {path}")
        except Exception as e:
            print(f"Error handling {model_id}: {e}")
            success = False

    # Download YOLO models
    try:
        from ultralytics import YOLO
        for yolo_model in YOLO_MODELS:
            print(f"\n--- Checking YOLO {yolo_model} ---")
            try:
                YOLO(yolo_model)
                print(f"YOLO Model {yolo_model} is ready.")
            except Exception as e:
                print(f"Error handling YOLO {yolo_model}: {e}")
                success = False
    except ImportError:
        print("\nWarning: ultralytics not installed. Skipping YOLO model download.")
    
    if success:
        print("\nAll models are downloaded and verified.")
    else:
        print("\nSome models failed to download. Please check your HF_TOKEN and internet connection.")
        sys.exit(1)

if __name__ == "__main__":
    check_and_download()
