"""
TrustKarat — Text Feature Extraction Engine
=============================================
Extracts structured signals from free-text user descriptions.
Fuses with audio/visual features in the XGBoost decision layer.

Handles inputs like:
    "ancient gold bangle from grandmother, very old"
    "bought from Tanishq last year, has 916 stamp"
    "looks dull, some scratches, not sure if real"
    "family heirloom, 22 carat, original bill available"
"""

import re
import numpy as np
from dataclasses import dataclass, asdict


# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE BASE — domain-specific gold vocabulary
# ══════════════════════════════════════════════════════════════════════════════

# Purity signals — explicit karat / fineness mentions
PURITY_PATTERNS = {
    # Numeric purity codes
    r"\b916\b":        {"karat": "22K", "purity": 91.6, "confidence": 0.95},
    r"\b750\b":        {"karat": "18K", "purity": 75.0, "confidence": 0.95},
    r"\b585\b":        {"karat": "14K", "purity": 58.5, "confidence": 0.95},
    r"\b875\b":        {"karat": "21K", "purity": 87.5, "confidence": 0.95},
    r"\b958\b":        {"karat": "23K", "purity": 95.8, "confidence": 0.95},
    r"\b375\b":        {"karat": "9K",  "purity": 37.5, "confidence": 0.95},
    r"\b999\b":        {"karat": "24K", "purity": 99.9, "confidence": 0.95},
    # Karat words
    r"\b24\s*k(arat)?\b": {"karat": "24K", "purity": 99.9, "confidence": 0.90},
    r"\b22\s*k(arat)?\b": {"karat": "22K", "purity": 91.6, "confidence": 0.90},
    r"\b21\s*k(arat)?\b": {"karat": "21K", "purity": 87.5, "confidence": 0.90},
    r"\b18\s*k(arat)?\b": {"karat": "18K", "purity": 75.0, "confidence": 0.90},
    r"\b14\s*k(arat)?\b": {"karat": "14K", "purity": 58.5, "confidence": 0.90},
    r"\b9\s*k(arat)?\b":  {"karat": "9K",  "purity": 37.5, "confidence": 0.90},
    # Indian vernacular
    r"\bchobis\s*carat\b": {"karat": "24K", "purity": 99.9, "confidence": 0.85},
    r"\bbais\s*carat\b":   {"karat": "22K", "purity": 91.6, "confidence": 0.85},
    r"\batharas\s*carat\b":{"karat": "18K", "purity": 75.0, "confidence": 0.85},
    # "carat" word variants (English)
    r"\b24\s*carat\b":     {"karat": "24K", "purity": 99.9, "confidence": 0.88},
    r"\b22\s*carat\b":     {"karat": "22K", "purity": 91.6, "confidence": 0.88},
    r"\b21\s*carat\b":     {"karat": "21K", "purity": 87.5, "confidence": 0.88},
    r"\b18\s*carat\b":     {"karat": "18K", "purity": 75.0, "confidence": 0.88},
    r"\b14\s*carat\b":     {"karat": "14K", "purity": 58.5, "confidence": 0.88},
}

# Trusted Indian jeweler brands — boosts authenticity score
TRUSTED_BRANDS = [
    "tanishq", "malabar", "kalyan", "png", "pc jeweller",
    "titan", "caratlane", "joyalukkas", "tbz", "grt",
    "bhima", "senco", "orra", "hazoorilal", "tribhovandas",
    "kishandas", "waman hari pethe",
]

# Document types — provenance signals
BILL_KEYWORDS = [
    "bill", "receipt", "invoice", "certificate", "kachi",
    "pucca", "hallmark certificate", "bis certificate",
    "original bill", "purchase bill", "warranty",
]

# Age / provenance signals
AGE_SIGNALS = {
    # Strong age indicators — increases wear/purity uncertainty
    "ancient":        {"age_years": 80,  "weight": -0.15, "purity_drift": -0.05},
    "antique":        {"age_years": 60,  "weight": -0.12, "purity_drift": -0.04},
    "heirloom":       {"age_years": 40,  "weight": -0.10, "purity_drift": -0.03},
    "grandmother":    {"age_years": 40,  "weight": -0.10, "purity_drift": -0.03},
    "grandfather":    {"age_years": 50,  "weight": -0.12, "purity_drift": -0.04},
    "inherited":      {"age_years": 30,  "weight": -0.08, "purity_drift": -0.02},
    "old":            {"age_years": 20,  "weight": -0.05, "purity_drift": -0.02},
    "vintage":        {"age_years": 30,  "weight": -0.08, "purity_drift": -0.03},
    "decades":        {"age_years": 30,  "weight": -0.08, "purity_drift": -0.03},
    "generation":     {"age_years": 25,  "weight": -0.06, "purity_drift": -0.02},
    # Recent purchase — high confidence
    "last year":      {"age_years": 1,   "weight": 0.0,   "purity_drift": 0.0},
    "last month":     {"age_years": 0,   "weight": 0.0,   "purity_drift": 0.0},
    "new":            {"age_years": 0,   "weight": 0.0,   "purity_drift": 0.0},
    "recently":       {"age_years": 1,   "weight": 0.0,   "purity_drift": 0.0},
    "just bought":    {"age_years": 0,   "weight": 0.0,   "purity_drift": 0.0},
}

# Condition signals
CONDITION_SIGNALS = {
    # Negative — reduces confidence
    "scratched":    {"condition": "worn",    "auth_delta": -0.08},
    "dull":         {"condition": "worn",    "auth_delta": -0.06},
    "worn":         {"condition": "worn",    "auth_delta": -0.07},
    "tarnished":    {"condition": "worn",    "auth_delta": -0.10},
    "damaged":      {"condition": "damaged", "auth_delta": -0.12},
    "repaired":     {"condition": "repaired","auth_delta": -0.05},
    "broken":       {"condition": "damaged", "auth_delta": -0.15},
    "faded":        {"condition": "worn",    "auth_delta": -0.08},
    "chipped":      {"condition": "damaged", "auth_delta": -0.10},
    "bent":         {"condition": "damaged", "auth_delta": -0.05},
    # Positive
    "polished":     {"condition": "good",    "auth_delta": +0.04},
    "shiny":        {"condition": "good",    "auth_delta": +0.03},
    "like new":     {"condition": "good",    "auth_delta": +0.06},
    "excellent":    {"condition": "good",    "auth_delta": +0.07},
    "clean":        {"condition": "good",    "auth_delta": +0.04},
    "well kept":    {"condition": "good",    "auth_delta": +0.05},
}

# Fraud / red flag signals
FRAUD_SIGNALS = {
    "fake":         {"fraud_flag": True,  "fraud_delta": -0.40},
    "plated":       {"fraud_flag": True,  "fraud_delta": -0.45},
    "gold plated":  {"fraud_flag": True,  "fraud_delta": -0.45},
    "imitation":    {"fraud_flag": True,  "fraud_delta": -0.40},
    "artificial":   {"fraud_flag": True,  "fraud_delta": -0.40},
    "duplicate":    {"fraud_flag": True,  "fraud_delta": -0.42},
    "not sure":     {"fraud_flag": False, "fraud_delta": -0.10},
    "not certain":  {"fraud_flag": False, "fraud_delta": -0.10},
    "suspicious":   {"fraud_flag": False, "fraud_delta": -0.15},
    "doubt":        {"fraud_flag": False, "fraud_delta": -0.12},
    "maybe real":   {"fraud_flag": False, "fraud_delta": -0.08},
}

# Jewelry type vocabulary
JEWELRY_TYPES = {
    "ring":      "ring",      "rings":      "ring",
    "bangle":    "bangle",    "bangles":    "bangle",
    "chain":     "chain",     "necklace":   "necklace",
    "earring":   "earring",   "earrings":   "earring",
    "bracelet":  "bracelet",  "anklet":     "anklet",
    "pendant":   "pendant",   "mangalsutra":"mangalsutra",
    "haar":      "necklace",  "kangan":     "bangle",
    "payal":     "anklet",    "jhumka":     "earring",
    "bajuband":  "armlet",    "maang tikka":"head_jewelry",
}


# ══════════════════════════════════════════════════════════════════════════════
# DATACLASS — structured output
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class TextFeatures:
    # Purity signals
    mentioned_karat:      str   = "Unknown"
    mentioned_purity:     float = 0.0
    purity_confidence:    float = 0.0

    # Provenance
    has_bill:             bool  = False
    trusted_brand:        str   = "None"
    brand_verified:       bool  = False

    # Age
    estimated_age_years:  float = 0.0
    age_signal:           str   = "Unknown"

    # Condition
    condition:            str   = "Unknown"
    condition_score:      float = 0.5      # 0 (bad) → 1 (good)

    # Fraud flags
    fraud_flag:           bool  = False
    fraud_signals_found:  list  = None

    # Jewelry type
    jewelry_type:         str   = "Unknown"

    # Overall text authenticity score (0–1)
    text_auth_score:      float = 0.5

    # Raw extracted signals for XGBoost
    feature_vector:       list  = None


# ══════════════════════════════════════════════════════════════════════════════
# MAIN EXTRACTOR
# ══════════════════════════════════════════════════════════════════════════════

def extract_text_features(description: str) -> TextFeatures:
    """
    Parse free-text description → structured TextFeatures.

    Example inputs:
        "My grandmother's ancient gold bangle, very old, 22 carat"
        "Bought from Tanishq, 916 hallmark, have the bill"
        "Looks a bit dull and scratched, not sure if real gold"
    """
    tf = TextFeatures(fraud_signals_found=[])

    if not description or not description.strip():
        tf.feature_vector = _build_vector(tf)
        return tf

    text = description.lower().strip()
    text = re.sub(r"[^\w\s\.\,\-\/]", " ", text)   # normalise
    auth_score = 0.50                                # start neutral

    # ── 1. Purity / Karat detection ─────────────────────────────────────
    for pattern, info in PURITY_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            tf.mentioned_karat   = info["karat"]
            tf.mentioned_purity  = info["purity"]
            tf.purity_confidence = info["confidence"]
            auth_score += 0.12   # explicit karat = positive signal
            break

    # ── 2. Brand detection ───────────────────────────────────────────────
    for brand in TRUSTED_BRANDS:
        if brand in text:
            tf.trusted_brand  = brand.title()
            tf.brand_verified = True
            auth_score += 0.15
            break

    # ── 3. Bill / document detection (with negation guard) ───────────────
    negation = r"\b(no|without|don.t have|dont have|missing|lost)\b"
    for kw in BILL_KEYWORDS:
        if kw in text:
            # Check if negated within 4 words before the keyword
            pattern = negation + r"[\w\s]{0,25}" + re.escape(kw)
            if not re.search(pattern, text):
                tf.has_bill = True
                auth_score += 0.10
            break

    # ── 4. Age signals ───────────────────────────────────────────────────
    best_age_match = None
    for keyword, info in AGE_SIGNALS.items():
        if keyword in text:
            if best_age_match is None or info["age_years"] > best_age_match["age_years"]:
                best_age_match    = info
                tf.age_signal     = keyword
    if best_age_match:
        tf.estimated_age_years = best_age_match["age_years"]
        auth_score += best_age_match["weight"]  # old items = more uncertainty

    # ── 5. Condition signals ──────────────────────────────────────────────
    cond_deltas   = []
    cond_labels   = []
    for keyword, info in CONDITION_SIGNALS.items():
        if keyword in text:
            cond_deltas.append(info["auth_delta"])
            cond_labels.append(info["condition"])
            auth_score += info["auth_delta"]

    if cond_labels:
        # Most severe condition wins
        if "damaged" in cond_labels:
            tf.condition = "damaged"
            tf.condition_score = 0.25
        elif "worn" in cond_labels:
            tf.condition = "worn"
            tf.condition_score = 0.45
        elif "repaired" in cond_labels:
            tf.condition = "repaired"
            tf.condition_score = 0.50
        elif "good" in cond_labels:
            tf.condition = "good"
            tf.condition_score = 0.85
    else:
        tf.condition = "not mentioned"
        tf.condition_score = 0.60

    # ── 6. Fraud signals ─────────────────────────────────────────────────
    for keyword, info in FRAUD_SIGNALS.items():
        if keyword in text:
            tf.fraud_signals_found.append(keyword)
            auth_score += info["fraud_delta"]
            if info["fraud_flag"]:
                tf.fraud_flag = True

    # ── 7. Jewelry type ──────────────────────────────────────────────────
    for word, jtype in JEWELRY_TYPES.items():
        if word in text:
            tf.jewelry_type = jtype
            break

    # ── 8. Clamp final auth score ─────────────────────────────────────────
    tf.text_auth_score = float(np.clip(auth_score, 0.0, 1.0))

    # ── 9. Build numeric feature vector for XGBoost ───────────────────────
    tf.feature_vector = _build_vector(tf)

    return tf


def _build_vector(tf: TextFeatures) -> list:
    """
    Convert TextFeatures → flat numeric vector for model fusion.
    Consistent 14-dimensional output regardless of input.
    """
    karat_enc = {
        "9K": 0, "14K": 1, "18K": 2, "21K": 3,
        "22K": 4, "23K": 5, "24K": 6, "Unknown": -1
    }
    type_enc = {
        "ring": 0, "bangle": 1, "chain": 2, "necklace": 3,
        "earring": 4, "bracelet": 5, "anklet": 6,
        "pendant": 7, "mangalsutra": 8,
        "armlet": 9, "head_jewelry": 10, "Unknown": -1
    }

    return [
        karat_enc.get(tf.mentioned_karat, -1),          # 0: karat class
        tf.mentioned_purity,                             # 1: purity %
        tf.purity_confidence,                            # 2: purity confidence
        int(tf.has_bill),                                # 3: bill exists
        int(tf.brand_verified),                          # 4: trusted brand
        min(tf.estimated_age_years / 80.0, 1.0),        # 5: age (normalised)
        tf.condition_score,                              # 6: condition
        int(tf.fraud_flag),                              # 7: hard fraud flag
        len(tf.fraud_signals_found) / 5.0,              # 8: fraud signal count
        tf.text_auth_score,                              # 9: overall auth score
        type_enc.get(tf.jewelry_type, -1),               # 10: jewelry type
        int(tf.mentioned_karat != "Unknown"),            # 11: purity mentioned
        int(tf.age_signal != "Unknown"),                 # 12: age mentioned
        int(tf.condition != "Unknown"),                  # 13: condition mentioned
    ]


# ══════════════════════════════════════════════════════════════════════════════
# EXPLANATION LAYER — judge-friendly output
# ══════════════════════════════════════════════════════════════════════════════

def explain(tf: TextFeatures) -> dict:
    """
    Human-readable explanation of what the text said and how it affected
    the assessment. This is what the NBFC officer sees.
    """
    factors = []
    risk_adj = "No change"

    if tf.mentioned_karat != "Unknown":
        factors.append(f"✅ Karat declared: {tf.mentioned_karat} ({tf.mentioned_purity}%)")

    if tf.brand_verified:
        factors.append(f"✅ Trusted jeweler mentioned: {tf.trusted_brand}")

    if tf.has_bill:
        factors.append("✅ Purchase document/bill mentioned")

    if tf.estimated_age_years > 30:
        factors.append(f"⚠ Old item (~{int(tf.estimated_age_years)} yrs) — higher purity uncertainty")
        risk_adj = "Slight increase in risk"

    if tf.estimated_age_years <= 2 and tf.estimated_age_years >= 0:
        if tf.age_signal != "Unknown":
            factors.append("✅ Recently purchased — lower risk")

    if tf.condition in ("worn", "damaged"):
        factors.append(f"⚠ Condition: {tf.condition} — weight may be lower than declared")

    if tf.fraud_flag:
        factors.append(f"🚨 Fraud keywords detected: {', '.join(tf.fraud_signals_found)}")
        risk_adj = "Significant risk increase"
    elif tf.fraud_signals_found:
        factors.append(f"⚠ Uncertainty keywords: {', '.join(tf.fraud_signals_found)}")
        risk_adj = "Moderate risk increase"

    if not factors:
        factors.append("ℹ No strong signals in description — using AI scan only")

    return {
        "text_auth_score":   round(tf.text_auth_score, 2),
        "risk_adjustment":   risk_adj,
        "signals_detected":  factors,
        "jewelry_type":      tf.jewelry_type,
        "karat_from_text":   tf.mentioned_karat,
        "has_bill":          tf.has_bill,
        "brand":             tf.trusted_brand,
        "condition":         tf.condition,
        "fraud_flag":        tf.fraud_flag,
        "estimated_age_yrs": int(tf.estimated_age_years),
    }


# ══════════════════════════════════════════════════════════════════════════════
# FUSION — merge text features into final decision
# ══════════════════════════════════════════════════════════════════════════════

def fuse_with_scores(
    text_features: TextFeatures,
    visual_score:  float,        # 0–100 from detector.py
    hallmark_score: float,       # 0–100 from ocr.py
    weight_conf:   float,        # 0–1 from weight.py
    audio_score:   float,        # 0–100 from audio.py
) -> dict:
    """
    Merge text signals with all model outputs → final risk + confidence.

    Weights:
        Hallmark (visual):  35%
        Text signals:       25%  ← THIS FILE
        Visual detection:   20%
        Audio:              12%
        Weight:             8%
    """
    # Text contribution
    text_score = tf_to_score(text_features)

    final = (
        hallmark_score * 0.35 +
        text_score     * 0.25 +
        visual_score   * 0.20 +
        audio_score    * 0.12 +
        weight_conf * 100 * 0.08
    )

    # Hard overrides
    if text_features.fraud_flag:
        final = min(final, 20)   # Force reject territory

    if text_features.has_bill and text_features.brand_verified:
        final = min(final + 8, 100)  # Bill + brand = bonus

    if text_features.estimated_age_years > 50:
        final = final * 0.92         # Age uncertainty penalty

    final = float(np.clip(final, 0, 100))

    if final >= 72:
        decision, color = "Pre-Approved", "green"
    elif final >= 50:
        decision, color = "Needs Verification", "orange"
    else:
        decision, color = "Reject", "red"

    return {
        "final_score":    round(final, 1),
        "decision":       decision,
        "decision_color": color,
        "score_breakdown": {
            "hallmark_score": round(hallmark_score, 1),
            "text_score":     round(text_score, 1),
            "visual_score":   round(visual_score, 1),
            "audio_score":    round(audio_score, 1),
            "weight_score":   round(weight_conf * 100, 1),
        }
    }


def tf_to_score(tf: TextFeatures) -> float:
    """Convert TextFeatures auth score to 0–100."""
    return float(np.clip(tf.text_auth_score * 100, 0, 100))


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_cases = [
        "Ancient gold bangle from my grandmother, very old, looks a bit dull",
        "Bought from Tanishq last year, 916 hallmark, have original bill",
        "22 carat ring, family heirloom, been in family for decades, slightly scratched",
        "Not sure if this is real gold or gold plated, looks fake",
        "Just bought this necklace from Malabar Gold last month, 18K, excellent condition",
        "Old chain, no bill, no hallmark visible, suspicious colour near clasp",
    ]

    print("\n" + "═" * 65)
    print("  TrustKarat — Text Feature Extraction Test")
    print("═" * 65)

    for desc in test_cases:
        print(f"\n📝 Input: \"{desc}\"")
        tf  = extract_text_features(desc)
        exp = explain(tf)
        print(f"   Auth Score: {exp['text_auth_score']}  |  "
              f"Karat: {exp['karat_from_text']}  |  "
              f"Fraud: {exp['fraud_flag']}  |  "
              f"Condition: {exp['condition']}")
        for s in exp["signals_detected"]:
            print(f"   {s}")
