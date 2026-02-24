import logging
import torch
import torch.nn.functional as F
import numpy as np
import cv2
from PIL import Image
import io
from app.services.medsiglip_service import medsiglip_service

logger = logging.getLogger(__name__)

class GradCAMService:
    def __init__(self):
        self.gradients = None
        self.activations = None
        self.hooks = []

    def _save_gradient(self, _module, _grad_input, grad_output):
        self.gradients = grad_output[0]

    def _save_activation(self, _module, _input, output):
        if isinstance(output, tuple):
             self.activations = output[0]
        else:
             self.activations = output

    def get_heatmap(self, image_content: bytes, target_label: str) -> bytes:
        """
        Generates a Grad-CAM heatmap for the given image and target label.
        Returns the overlay image as bytes (JPEG).
        """
        # Ensure model is ready
        medsiglip_service._load_model()
        model = medsiglip_service.model
        processor = medsiglip_service.processor
        device = medsiglip_service.device

        # Clean state
        self.gradients = None
        self.activations = None
        for h in self.hooks: h.remove()
        self.hooks = []

        try:
            # Prepare Inputs
            image = Image.open(io.BytesIO(image_content)).convert("RGB")
            inputs = processor(text=[target_label], images=image, return_tensors="pt", padding="max_length").to(device)
            
            # Hook Target Layer: Last Encoder Layer of Vision Model
            target_layer = model.vision_model.encoder.layers[-1]
            
            h1 = target_layer.register_forward_hook(self._save_activation)
            h2 = target_layer.register_full_backward_hook(self._save_gradient)
            self.hooks.extend([h1, h2])

            # Forward Pass
            model.zero_grad()
            outputs = model(**inputs)
            
            # Calculate Score
            score = outputs.logits_per_image[0, 0]
            
            # Backward Pass
            score.backward()
            
            if self.gradients is None or self.activations is None:
                logger.error("Failed to capture gradients or activations.")
                return image_content

            # CPU processing
            gradients = self.gradients[0].detach().cpu()
            activations = self.activations[0].detach().cpu()
            
            weights = torch.mean(gradients, dim=0)
            cam = torch.matmul(activations, weights)
            
            seq_len = cam.shape[0]
            grid_size = int(seq_len**0.5)
            
            if grid_size * grid_size != seq_len:
                logger.warning(f"Non-square sequence length: {seq_len}")
                return image_content
            
            cam_map = cam.view(grid_size, grid_size)
            cam_map = F.relu(cam_map)
            
            if cam_map.max() > 0:
                cam_map = cam_map - cam_map.min()
                cam_map = cam_map / cam_map.max()
            
            cam_map_np = cam_map.numpy()

            img_np = np.array(image)
            heatmap = cv2.resize(cam_map_np, (img_np.shape[1], img_np.shape[0]))
            
            heatmap = np.uint8(255 * heatmap)
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            overlay = cv2.addWeighted(img_np, 0.6, heatmap_color, 0.4, 0)
            
            out_img = Image.fromarray(overlay)
            buf = io.BytesIO()
            out_img.save(buf, format="JPEG")
            return buf.getvalue()

        except Exception as e:
            logger.error(f"Grad-CAM error: {e}")
            return image_content
        finally:
            for h in self.hooks: h.remove()
            self.hooks = []

gradcam_service = GradCAMService()
