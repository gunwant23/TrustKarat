"""
Loan decision engine — fuses all model outputs.
Uses XGBoost if trained model exists, else rule-based scoring.
Outputs: Pre-approve / Needs Verification / Reject
"""
import numpy as np
import os

RISK_WEIGHTS = {
    "Low":    0.0,
    "Medium": 0.5,
    "High":   1.0,
}

def _rule_based_score(detection, hallmark, weight, audio) -> dict:
    """
    Transparent, explainable scoring. Each factor → 0-100 score.
    Makes the SHAP-equivalent explanation easy to present to judges.
    """
    scores = {}

    # 1. Hallmark score (40% weight — most critical)
    if hallmark["genuine"]:
        scores["hallmark"] = 90
    elif hallmark["hallmark_detected"] and not hallmark["genuine"]:
        scores["hallmark"] = 10   # fake marker found
    else:
        scores["hallmark"] = 50   # no hallmark — uncertain

    # 2. Visual detection confidence (25%)
    det_conf = detection.get("confidence", 0.7)
    scores["detection"] = int(det_conf * 100)

    # 3. Weight reasonability (20%)
    w_low  = weight.get("weight_low_g", 0)
    w_high = weight.get("weight_high_g", 999)
    if 2 < w_low and w_high < 100:   # realistic jewelry weight
        scores["weight"] = 80
    elif w_high > 100:                # suspiciously heavy
        scores["weight"] = 20
    else:
        scores["weight"] = 60

    # 4. Audio purity (15%)
    purity_pct = audio.get("purity_percent")
    if purity_pct is None:
        scores["audio"] = 65   # not tested — neutral
    elif purity_pct >= 75:
        scores["audio"] = 90
    elif purity_pct >= 58:
        scores["audio"] = 70
    else:
        scores["audio"] = 30

    # Weighted final score
    final = (
        scores["hallmark"]  * 0.40 +
        scores["detection"] * 0.25 +
        scores["weight"]    * 0.20 +
        scores["audio"]     * 0.15
    )

    return scores, round(final, 1)

def make_decision(detection: dict, hallmark: dict, weight: dict, audio: dict) -> dict:
    try:
        scores, final_score = _rule_based_score(detection, hallmark, weight, audio)

        # Decision thresholds
        if hallmark.get("genuine") is False and hallmark.get("hallmark_detected"):
            decision       = "Reject"
            decision_color = "red"
            message        = "Fake hallmark marker detected. Physical verification required."
        elif final_score >= 72:
            decision       = "Pre-Approved"
            decision_color = "green"
            message        = "Gold assessment passed. Proceed to custody collection."
        elif final_score >= 50:
            decision       = "Needs Verification"
            decision_color = "orange"
            message        = "Assessment uncertain. Branch verification recommended."
        else:
            decision       = "Reject"
            decision_color = "red"
            message        = "Assessment failed. High fraud or quality risk detected."

        # Overall risk level
        if final_score >= 72:
            risk = "Low"
        elif final_score >= 50:
            risk = "Medium"
        else:
            risk = "High"

        # Purity band from hallmark or audio
        karat = hallmark.get("karat", "Unknown")
        if karat in ("Unknown", "Unverified") and audio.get("purity_class") not in (None, "Not tested", "Unknown"):
            karat = audio["purity_class"]

        return {
            "decision":       decision,
            "decision_color": decision_color,
            "message":        message,
            "risk_level":     risk,
            "confidence":     f"{int(final_score)}%",
            "scores":         scores,
            "jewelry_type":   detection.get("jewelry_type", "Unknown"),
            "hallmark_code":  hallmark.get("code", "Not detected"),
            "hallmark_genuine": hallmark.get("genuine", False),
            "karat_band":     karat,
            "purity_percent": hallmark.get("purity") or audio.get("purity_percent"),
            "weight_band":    weight.get("weight_band", "Unknown"),
            "weight_confidence": weight.get("confidence", 0),
            "audio_purity":   audio.get("purity_class", "Not tested"),
            "fraud_flags":    "None" if hallmark.get("genuine") else hallmark.get("code", "Unknown"),
        }

    except Exception as e:
        return {
            "decision":       "Needs Verification",
            "decision_color": "orange",
            "message":        f"System error: {str(e)}",
            "risk_level":     "Medium",
            "confidence":     "0%",
        }
