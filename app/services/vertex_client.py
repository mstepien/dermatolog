import os
import logging
try:
    from google.cloud import aiplatform
    from google.oauth2 import service_account
    import google.auth
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    aiplatform = None
    service_account = None
    google = None

logger = logging.getLogger(__name__)

class VertexClient:
    def __init__(self):
        self.project_id = os.environ.get("PROJECT_ID")
        self.location = os.environ.get("LOCATION", "us-central1")
        self.endpoint_id = os.environ.get("ENDPOINT_ID") # ID of the deployed MedGemma endpoint
        self.credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        
        self.setup_complete = False
        
        if not GOOGLE_CLOUD_AVAILABLE:
            logger.warning("google-cloud-aiplatform not installed. Vertex AI client will be mocked.")
            return

        if self.project_id:
            try:
                # If credentials path is set, explicit load (dev), else default (cloud run)
                if self.credentials_path and os.path.exists(self.credentials_path):
                    creds = service_account.Credentials.from_service_account_file(self.credentials_path)
                else:
                    creds, _ = google.auth.default()

                aiplatform.init(
                    project=self.project_id,
                    location=self.location,
                    credentials=creds
                )
                self.setup_complete = True
                logger.info(f"Vertex AI initialized for project {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {e}")

    async def predict(self, prompt: str, max_tokens: int = 256, temperature: float = 0.2) -> str:
        if not self.setup_complete:
            logger.info("Returning mock prediction because Vertex AI is not configured.")
            return "Mock Response: Vertex AI is not configured. This is a dummy prediction."
        
        if not self.endpoint_id:
            return "Endpoint ID not configured."

        try:
            # Get Endpoint
            endpoint = aiplatform.Endpoint(self.endpoint_id)
            
            # Predict
            # Structure depends on the model serving container. 
            # MedGemma usually expects instances=[{"prompt": ...}]
            instances = [{"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}]
            
            response = endpoint.predict(instances=instances)
            
            # Parse prediction (assuming standard format, adjust based on actual model output)
            # Typically response.predictions is a list
            if response.predictions:
                 return str(response.predictions[0])
            else:
                 return "No prediction returned."

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise e

vertex_client = VertexClient()
