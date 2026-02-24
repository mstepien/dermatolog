import pytest
import math
from app.services.result_interpreter import result_interpreter

def test_interpret_high_risk_detected():
    # Case where Melanoma and BCC are the top 2
    # Margin: (0.45 + 0.40) - 0.15 = 0.70 -> Confidence Class: Confident (> 40%)
    results = [
        {"label": "Melanoma", "score": 0.45},
        {"label": "Basal Cell Carcinoma", "score": 0.40},
        {"label": "Normal Skin", "score": 0.15}
    ]
    interpretation = result_interpreter.interpret(results)
    assert interpretation["is_high_risk"] is True
    assert interpretation["annotation"] == "High likeness of tumor disease"
    assert interpretation["color_hint"] == "red"
    # New rule: Margin is 0.70, so it's Confident
    assert interpretation["confidence_label"] == "Confident"
    assert interpretation["margin"] == 0.70

def test_tumor_consolidation_rule():
    # Multiple tumor classes at the top
    results = [
        {"label": "Melanoma", "score": 0.30},
        {"label": "Basal Cell Carcinoma", "score": 0.25},
        {"label": "Squamous Cell Carcinoma", "score": 0.20},
        {"label": "Atopic Dermatitis", "score": 0.15},
        {"label": "Normal Skin", "score": 0.10}
    ]
    # Sum of tumors = 0.30 + 0.25 + 0.20 = 0.75
    # Next non-tumor = 0.15
    # Margin = 0.75 - 0.15 = 0.60
    interpretation = result_interpreter.interpret(results)
    assert interpretation["margin"] == 0.60
    assert interpretation["confidence_label"] == "Confident"
    assert interpretation["is_high_risk"] is True

def test_margin_confidence_tiers():
    # 1. Confident (Margin > 40%)
    # 40.1% -> Confident
    res_401 = [{"label": "A", "score": 0.501}, {"label": "B", "score": 0.10}]
    assert result_interpreter.interpret(res_401)["confidence_label"] == "Confident"
    
    # 2. Plausible (40% >= Margin > 25%)
    # 40.0% -> Plausible
    res_400 = [{"label": "A", "score": 0.50}, {"label": "B", "score": 0.10}]
    assert result_interpreter.interpret(res_400)["confidence_label"] == "Plausible"
    # 25.1% -> Plausible
    res_251 = [{"label": "A", "score": 0.351}, {"label": "B", "score": 0.10}]
    assert result_interpreter.interpret(res_251)["confidence_label"] == "Plausible"
    
    # 3. Low confidence (20% >= Margin > 10%)
    # 20.0% -> Low confidence
    res_200 = [{"label": "A", "score": 0.30}, {"label": "B", "score": 0.10}]
    assert result_interpreter.interpret(res_200)["confidence_label"] == "Low confidence"
    # 10.1% -> Low confidence
    res_101 = [{"label": "A", "score": 0.201}, {"label": "B", "score": 0.10}]
    assert result_interpreter.interpret(res_101)["confidence_label"] == "Low confidence"
    
    # 4. Results unclear (10% >= Margin)
    # 10.0% -> Results unclear
    res_100 = [{"label": "A", "score": 0.20}, {"label": "B", "score": 0.10}]
    assert result_interpreter.interpret(res_100)["confidence_label"] == "Results unclear"
    # 5.0% -> Results unclear
    res_050 = [{"label": "A", "score": 0.15}, {"label": "B", "score": 0.10}]
    assert result_interpreter.interpret(res_050)["confidence_label"] == "Results unclear"

def test_interpret_not_clear_mixed():
    # Case: Top 1 is Tumor, Top 2 is Non-Tumor, Margin is small (0.01)
    results = [
        {"label": "Melanoma", "score": 0.34},
        {"label": "Melanocytic Nevus", "score": 0.33},
        {"label": "Normal Skin", "score": 0.33}
    ]
    # Margin is 0.01 < margin_threshold (default 0.05)
    interpretation = result_interpreter.interpret(results)
    assert interpretation["annotation"] == "Not clear"
    assert interpretation["color_hint"] == "yellow"
    assert interpretation["status"] == "uncertain_mixed"
    assert interpretation["confidence_label"] == "Results unclear"

def test_interpret_clear_tumor():
    # Top 1 is Tumor, Top 2 is Non-Tumor, Margin is large (0.60)
    results = [
        {"label": "Melanoma", "score": 0.80},
        {"label": "Melanocytic Nevus", "score": 0.20}
    ]
    interpretation = result_interpreter.interpret(results)
    assert "Potential cancerous condition" in interpretation["annotation"]
    assert interpretation["confidence_label"] == "Confident"

def test_interpret_low_risk():
    # Both top 2 are non-tumor, Margin: 0.20
    results = [
        {"label": "Psoriasis", "score": 0.50},
        {"label": "Atopic Dermatitis", "score": 0.30},
        {"label": "Melanoma", "score": 0.20}
    ]
    interpretation = result_interpreter.interpret(results)
    assert interpretation["is_high_risk"] is False
    assert "No immediate tumor likeness detected" in interpretation["annotation"]
    assert interpretation["confidence_label"] == "Low confidence"

def test_entropy_values():
    results_uniform = [{"label": f"L{i}", "score": 0.125} for i in range(8)]
    interpretation = result_interpreter.interpret(results_uniform)
    assert pytest.approx(interpretation["entropy"], 0.01) == 3.0
    assert interpretation["is_reliable"] is False
    assert "No immediate tumor likeness detected" in interpretation["annotation"]
    assert any("Low confidence" in line for line in interpretation["computation_process"])
    assert any("3.00" in line for line in interpretation["computation_process"])

def test_empty_results():
    interpretation = result_interpreter.interpret([])
    assert interpretation["confidence_label"] == "Unknown"
    assert interpretation["color_hint"] == "gray"

def test_boundary_entropy():
    results = [{"label": "A", "score": 0.5}, {"label": "B", "score": 0.5}]
    interpretation = result_interpreter.interpret(results)
    assert interpretation["entropy"] == 1.0
    assert interpretation["is_reliable"] is True
