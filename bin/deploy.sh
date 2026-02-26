#!/bin/bash
set -e


# Load .env file if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Check for PROJECT_ID
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "your-project-id" ]; then
  echo "Error: PROJECT_ID is not set. Please set it in .env or export it."
  echo "Example: export PROJECT_ID=my-gcp-project-id"
  exit 1
fi

GOOGLE_CLOUD_PROJECT=$PROJECT_ID
SERVICE_NAME="${SERVICE_NAME:-medgemma-app}"
REGION="${REGION:-europe-west1}"
REPOSITORY="${REPOSITORY:-dermatolog-scan}"

# Hardware Configuration
MEMORY="${MEMORY:-8Gi}" 
CPU="${CPU:-4}"

echo "========================================================"
echo "   Deploying $SERVICE_NAME to Cloud Run ($REGION)"
echo "   Mode: Self-Contained (Local Inference)"
echo "========================================================"

# Image path in Artifact Registry
IMAGE_PATH="$REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$REPOSITORY/$SERVICE_NAME"

# 1. Build and Submit Container (Using Cloud Build)
echo "[1/3] Building container image..."
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_HF_TOKEN="$HF_TOKEN",_SERVICE_NAME="$SERVICE_NAME",_REPOSITORY="$REPOSITORY",_REGION="$REGION" .

# 2. Deploy to Cloud Run
echo "[2/3] Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_PATH \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --cpu-boost \
  --max-instances 1 \
  --timeout 300 \
  --concurrency 10 \
  --port 8080 \
  --set-env-vars="HF_TOKEN=$HF_TOKEN" 
  # Note: If HF_TOKEN is not set in your local shell, this will be empty.
  # The app handles missing token by falling back to public model.

echo "========================================================"
echo "   Deployment Complete!"
echo "========================================================"
