import logging
import torch
import os
from PIL import Image
from transformers import AutoProcessor, AutoModel
import io
from typing import List, Optional
from app.services.image_preprocess_service import image_preprocess_service
from app.config import MEDSIGLIP_MODEL_NAME, MODEL_IMAGE_SIZE

logger = logging.getLogger(__name__)

class MedSigLIPService:
    def __init__(self, model_name=MEDSIGLIP_MODEL_NAME):
        # We'll lazy load the model to avoid startup costs and potential auth issues crashing the app immediately
        self.model_name = model_name
        
        self.processor = None
        self.model = None
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading MedSigLIP model: {self.model_name} on {self.device}...")
            try:
                token = os.getenv("HF_TOKEN")
                self.processor = AutoProcessor.from_pretrained(self.model_name, token=token)
                self.model = AutoModel.from_pretrained(self.model_name, token=token).to(self.device)
                logger.info("MedSigLIP model loaded successfully.")
            except Exception as e:
                    logger.error(f"Failed to load MedSigLIP model: {e}")
                    raise e

    def get_embeddings(self, image_bytes: bytes, texts: Optional[List[str]] = None):
        """
        Run inference to get embeddings or probabilities for zero-shot classification.
        If texts is provided, performs zero-shot classification via similarity.
        """
        self._load_model()
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image = image_preprocess_service.prepare_image(image, MODEL_IMAGE_SIZE)
            
            if texts:
                # 64-token limit check as per requirements
                inputs = self.processor(
                    text=texts,
                    images=image,
                    padding="max_length",
                    max_length=64,
                    truncation=True,
                    return_tensors="pt"
                ).to(self.device)

                # Optional: Log warning if truncation occurred (check input_ids shape vs max_length)
                # Note: with truncation=True, the shape will be (num_texts, 64)
                # To detect if it *would* have exceeded, we could tokenize without truncation first,
                # but that's expensive. Instead, we can just ensure we stay within the limit.
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                # Retrieve logits
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
                
                # Format results
                results = []
                prob_values = probs[0].tolist()
                for i, text in enumerate(texts):
                    results.append({"label": text, "score": prob_values[i]})
                
                # Sort by score descending
                results.sort(key=lambda x: x["score"], reverse=True)
                return results
            else:
                # Just image embedding
                # MedSigLIP is a CLIP-like model, so we can get features
                inputs = self.processor(images=image, return_tensors="pt").to(self.device) # Only image
                with torch.no_grad():
                     image_features = self.model.get_image_features(**inputs)
                
                return {"embedding": image_features[0].tolist()}

        except Exception as e:
            logger.error(f"MedSigLIP inference failed: {e}")
            raise e

# Global instance
medsiglip_service = MedSigLIPService()
