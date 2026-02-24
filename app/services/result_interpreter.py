import math
import logging
from typing import List, Dict, Any
from app.dermatology_data import CANCEROUS_TUMOR_CLASSES
from app.config import INTERPRETER_ENTROPY_THRESHOLD, INTERPRETER_MARGIN_THRESHOLD, CONFIDENCE_CLASSES

logger = logging.getLogger(__name__)

class ResultInterpreter:
    """
    Analyzes classification results from MedSigLIP models to provide clinical insights.
    
    Responsibilities:
    1. Detect if top predictions indicate tumor-related diseases based on CANCEROUS_TUMOR_CLASSES.
    2. Handle mixed cases (Tumor vs Non-Tumor) with confidence margins.
    3. Calculate Predictive Entropy (Shannon Entropy) as a measure of model uncertainty.
    4. Provide descriptive annotations and color hints for UI.
    5. Classify confidence based on Top-1 vs Top-2 margin.
    """

    def interpret(self, results: List[Dict[str, Any]], 
                  entropy_threshold: float = INTERPRETER_ENTROPY_THRESHOLD,
                  margin_threshold: float = INTERPRETER_MARGIN_THRESHOLD) -> Dict[str, Any]:
        """Interprets a list of classification results."""
        if not results:
            return self._empty_result()

        scores = [r["score"] for r in results]
        entropy = self.calculate_entropy(scores)
        is_reliable = entropy < entropy_threshold

        # Rule 1: Margin Calculation (including Tumor Consolidation)
        margin = self._calculate_margin(results)
        conf_info = self.get_confidence_level(margin)
        
        # Rule 2: Status and Annotation Logic
        analysis = self._determine_status_and_annotation(results, margin, margin_threshold)
        
        # Rule 3: Format computation process for tech logs
        comp_process = self._format_computation_process(
            results, margin, margin_threshold, conf_info, entropy, entropy_threshold, is_reliable
        )

        return {
            "is_high_risk": analysis["is_high_risk"],
            "entropy": entropy,
            "is_reliable": is_reliable,
            "annotation": analysis["annotation"],
            "color_hint": analysis["color_hint"],
            "confidence_label": conf_info["label"],
            "confidence_color": conf_info["color_hint"],
            "status": analysis["status"],
            "margin": margin,
            "margin_threshold": margin_threshold,
            "computation_process": comp_process,
            "top_2_labels": [results[0]["label"], results[1]["label"]] if len(results) > 1 else [results[0]["label"], "None"]
        }

    def _empty_result(self) -> Dict[str, Any]:
        return {
            "is_high_risk": False, "entropy": 0.0, "is_reliable": False,
            "annotation": "No results available to interpret.", "color_hint": "gray",
            "confidence_label": "Unknown", "confidence_color": "gray",
            "computation_process": ["No results provided."]
        }

    def _calculate_margin(self, results: List[Dict[str, Any]]) -> float:
        """
        Calculates margin. 
        Tumor rule: sum(contiguous tumors) - first_non_tumor
        Default rule: top_1 - top_2
        """
        top_1 = results[0]
        if top_1["label"] in CANCEROUS_TUMOR_CLASSES:
            tumor_sum = 0.0
            next_non_tumor_score = 0.0
            found_non_tumor = False
            for r in results:
                if not found_non_tumor and r["label"] in CANCEROUS_TUMOR_CLASSES:
                    tumor_sum += r["score"]
                elif not found_non_tumor:
                    next_non_tumor_score = r["score"]
                    found_non_tumor = True
            return round(tumor_sum - next_non_tumor_score, 4)
        
        top_2_score = results[1]["score"] if len(results) > 1 else 0.0
        return round(top_1["score"] - top_2_score, 4)

    def _determine_status_and_annotation(self, results: List[Dict[str, Any]], margin: float, margin_threshold: float) -> Dict[str, Any]:
        """Provides status, annotation, and color hint based on top results."""
        t1 = results[0]
        t2 = results[1] if len(results) > 1 else {"label": "None", "score": 0.0}
        
        is_t1_tumor = t1["label"] in CANCEROUS_TUMOR_CLASSES
        is_t2_tumor = t2["label"] in CANCEROUS_TUMOR_CLASSES

        if is_t1_tumor and is_t2_tumor:
            return {"is_high_risk": True, "annotation": "High likeness of tumor disease", "color_hint": "red", "status": "tumor_detected"}
        
        if is_t1_tumor != is_t2_tumor:
            if margin < margin_threshold:
                return {"is_high_risk": False, "annotation": "Not clear", "color_hint": "yellow", "status": "uncertain_mixed"}
            
            if is_t1_tumor:
                return {"is_high_risk": False, "annotation": f"Potential cancerous condition: {t1['label']}", "color_hint": "red", "status": "potential_tumor"}
            return {"is_high_risk": False, "annotation": f"Likely benign: {t1['label']}", "color_hint": "green", "status": "likely_benign"}
            
        return {"is_high_risk": False, "annotation": "No immediate tumor likeness detected in top results", "color_hint": "green", "status": "benign"}

    def _format_computation_process(self, results, margin, margin_threshold, conf_info, entropy, entropy_threshold, is_reliable) -> List[str]:
        """Formats the detailed steps of interpretation for UI display."""
        t1 = results[0]
        t2 = results[1] if len(results) > 1 else {"label": "None", "score": 0.0}
        
        process = [
            f"Top 1: {t1['label']} ({t1['score']:.2f}) - Tumor: {t1['label'] in CANCEROUS_TUMOR_CLASSES}",
            f"Top 2: {t2['label']} ({t2['score']:.2f}) - Tumor: {t2['label'] in CANCEROUS_TUMOR_CLASSES}",
            f"Margin: {margin:.4f} (Threshold: {margin_threshold})",
            f"Confidence: {conf_info['label']}",
            f"Mixed Case Detect: {'Yes' if (t1['label'] in CANCEROUS_TUMOR_CLASSES) != (t2['label'] in CANCEROUS_TUMOR_CLASSES) else 'No'}",
            f"Entropy: {entropy:.2f} bits (Limit: {entropy_threshold})"
        ]
        process.append("Status: Prediction within reliability limits" if is_reliable else f"Status: Low confidence - High uncertainty detected (Entropy: {entropy:.2f})")
        return process

    def get_confidence_level(self, margin: float) -> Dict[str, str]:
        """
        Maps margin to a qualitative confidence level using thresholds from config.
        """
        # Round to avoid floating point precision issues (e.g. 0.4 - 0.1 = 0.30000000000000004)
        m = round(margin, 4)
        
        for cls in CONFIDENCE_CLASSES:
            if m > cls["min"]:
                return {
                    "label": cls["label"],
                    "color_hint": cls.get("color_hint", "")
                }
        
        # Fallback to the last class (usually 0.0) if no match found
        last_cls = CONFIDENCE_CLASSES[-1]
        return {
            "label": last_cls["label"],
            "color_hint": last_cls.get("color_hint", "")
        }

    def calculate_entropy(self, probabilities: List[float]) -> float:
        """
        Calculates Shannon entropy in bits.
        H = -sum(pi * log2(pi))
        """
        entropy = 0.0
        for p in probabilities:
            if p > 1e-9: # Avoid log(0)
                entropy -= p * math.log2(p)
        return entropy

# Global singleton instance
result_interpreter = ResultInterpreter()
