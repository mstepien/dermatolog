"""
Configuration settings for the Dermatolog AI Scan application.
Contains model parameters, clinical thresholds, and system constants.
"""


# --- Stage 2: Result Interpretation Parameters ---

# Shannon Entropy threshold (in bits) for determining prediction reliability.
# Entropy measures the model's "confusion" across all classes.
# For a 10-class distribution:
# - Max entropy (complete guessing) is ~3.32 bits.
# - High confidence (90% in one class) approaches 0 bits.
# Threshold of 2.5 allows for relative clarity but flags high-chaos distributions.
INTERPRETER_ENTROPY_THRESHOLD = 2.5

# Margin threshold specifically for Mixed (Tumor vs Non-Tumor) cases.
# If the top prediction is a tumor but the second is non-tumor (or vice versa),
# and the absolute difference in their scores is less than this value,
# the result is annotated as "Not clear".
INTERPRETER_MARGIN_THRESHOLD = 0.05

# --- Confidence Classification (Margin Based) ---

# Mapping of confidence levels based on the margin between Top-1 and Top-2 results.
# Used to provide qualitative feedback to the end user.
CONFIDENCE_CLASSES = [
    {"min": 0.40, "label": "Confident", "color_hint": "green"},
    {"min": 0.20, "label": "Plausible", "color_hint": "gray"},
    {"min": 0.10, "label": "Low confidence", "color_hint": "yellow"},
    {"min": 0.00, "label": "Results unclear", "color_hint": "red"},
]


# --- Model Configuration ---

# The target image resolution for MedSigLIP. 
# Changing this requires a compatible model checkpoint.
MODEL_IMAGE_SIZE = (448, 448)

# The default HuggingFace model path for MedSigLIP.
MEDSIGLIP_MODEL_NAME = "google/medsiglip-448"


