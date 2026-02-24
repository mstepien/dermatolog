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
SERVICE_NAME="dermatolog-ai-scan"
REGION="us-central1"
# We need enough memory for the model (MedSigLIP) to load.
# 4GB is the absolute minimum, 8GB is safer.
MEMORY="8Gi" 
CPU="2"

echo "========================================================"
echo "   Deploying $SERVICE_NAME to Cloud Run ($REGION)"
echo "   Mode: Self-Contained (Local Inference)"
echo "========================================================"

# 1. Build and Submit Container (Using Cloud Build to inject build args)
echo "[1/3] Building container image..."
gcloud builds submit --config cloudbuild.yaml --substitutions=_HF_TOKEN="$HF_TOKEN",_SERVICE_NAME="$SERVICE_NAME" .

# 2. Deploy to Cloud Run
echo "[2/3] Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/$SERVICE_NAME \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory $MEMORY \
  --cpu $CPU \
  --timeout 300 \
  --concurrency 10 \
  --set-env-vars="HF_TOKEN=$HF_TOKEN" 
  # Note: If HF_TOKEN is not set in your local shell, this will be empty.
  # The app handles missing token by falling back to public model.

echo "========================================================"
echo "   Deployment Complete!"
echo "========================================================"
