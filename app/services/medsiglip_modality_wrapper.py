import logging
from typing import List, Dict, Optional, Any
from app.services.medsiglip_service import medsiglip_service
from app.dermatology_data import MEDSIGLIP_DERMATOLOGY_NARROW_LABELS

logger = logging.getLogger(__name__)

class ClinicalModalityWrapper:
    """
    Generic wrapper for vision-language models that implements clinical modality templating
    using the MEDSIGLIP_DERMATOLOGY_NARROW_LABELS map (Keys and Values).
    """
    def __init__(self, service: Any, modality: str = "macroscopic"):
        self.service = service
        # "macroscopic" -> "Clinical photograph showing {desc}."
        # "dermoscopy" -> "Dermoscopy image revealing {desc}."
        self.modality = modality
        self.labels_map = MEDSIGLIP_DERMATOLOGY_NARROW_LABELS

    def _get_template(self) -> str:
        if self.modality == "dermoscopy":
            return "Dermoscopy image revealing {}."
        #return "Clinical photograph showing {}."
        return "A patient-submitted smartphone photograph showing {}."

    def analyze_image(self, image_bytes: bytes, custom_labels: Optional[List[str]] = None) -> List[Dict]:
        """
        Analyzes an image using clinical descriptions (values) wrapped in modality templates.
        Returns mapped results with original short labels (keys).
        """
        # 1. Prepare labels and descriptions from MEDSIGLIP_DERMATOLOGY_NARROW_LABELS
        if custom_labels:
            descriptions = []
            valid_labels = []
            for label in custom_labels:
                if label in self.labels_map:
                    descriptions.append(self.labels_map[label])
                    valid_labels.append(label)
                else:
                    # If not in our clinical map, use original label as description
                    descriptions.append(label)
                    valid_labels.append(label)
        else:
            # Use all predefined clinical labels (Keys and Values)
            valid_labels = list(self.labels_map.keys())
            descriptions = list(self.labels_map.values())

        # 2. Apply modality template to descriptions (Values)
        template = self._get_template()
        prompts = [template.format(desc) for desc in descriptions]

        print(f"\n[DEBUG] Prompts for {self.service.model_name}:")
        for p in prompts:
            print(f"  - {p}")

        # 3. Call the underlying service
        # Handle different method names between MedSigLIP and SigLIP services
        if hasattr(self.service, "get_embeddings"):
            raw_results = self.service.get_embeddings(image_bytes, texts=prompts)
        elif hasattr(self.service, "get_predictions"):
            raw_results = self.service.get_predictions(image_bytes, texts=prompts)
        else:
            raise AttributeError(f"Service {type(self.service)} has no supported inference method.")

        # 4. Map prompts back to original short labels (Keys)
        prompt_to_label = dict(zip(prompts, valid_labels))

        mapped_results = []
        for res in raw_results:
            original_label = prompt_to_label.get(res["label"], res["label"])
            mapped_results.append({
                "label": original_label,
                "description": res["label"], # The full prompt used
                "score": res["score"]
            })

        return mapped_results

# Global instances for easy access
medsiglip_wrapped_service = ClinicalModalityWrapper(medsiglip_service)
