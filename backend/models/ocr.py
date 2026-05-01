"""
Hallmark stamp OCR using EasyOCR.
Reads karat codes (916, 750, 585) and detects fake markers (GP, GF, GEP).
"""
import easyocr
import cv2
import numpy as np
import re

_reader = None

GENUINE_CODES = {
    "916": {"karat": "22K", "purity": 91.6, "risk": "Low"},
    "750": {"karat": "18K", "purity": 75.0, "risk": "Low"},
    "585": {"karat": "14K", "purity": 58.5, "risk": "Low"},
    "875": {"karat": "21K", "purity": 87.5, "risk": "Low"},
    "958": {"karat": "23K", "purity": 95.8, "risk": "Low"},
    "375": {"karat": "9K",  "purity": 37.5, "risk": "Low"},
    "22K": {"karat": "22K", "purity": 91.6, "risk": "Low"},
    "18K": {"karat": "18K", "purity": 75.0, "risk": "Low"},
    "14K": {"karat": "14K", "purity": 58.5, "risk": "Low"},
}

FAKE_MARKERS = ["GP", "GF", "GEP", "RGP", "HGP", "GLD", "PLATED", "FILLED"]

def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader

def _preprocess(image_path: str):
    """Enhance image for better OCR on stamps."""
    img = cv2.imread(image_path)
    if img is None:
        return None, None
    gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # CLAHE for contrast on gold stamps
    clahe   = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    # Threshold to isolate stamp ink
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img, thresh

def read_hallmark(image_path: str) -> dict:
    try:
        reader        = _get_reader()
        img, enhanced = _preprocess(image_path)

        # Run OCR on both original and enhanced
        texts = []
        results_orig = reader.readtext(image_path, detail=0, paragraph=False)
        texts.extend(results_orig)

        if enhanced is not None:
            results_enh = reader.readtext(enhanced, detail=0, paragraph=False)
            texts.extend(results_enh)

        # Flatten and uppercase all text
        all_text = " ".join(texts).upper()

        # Check for genuine codes
        for code, info in GENUINE_CODES.items():
            if code in all_text:
                return {
                    "hallmark_detected": True,
                    "code":    code,
                    "karat":   info["karat"],
                    "purity":  info["purity"],
                    "genuine": True,
                    "risk":    info["risk"],
                    "raw_text": all_text[:80],
                }

        # Check for fake markers
        for fake in FAKE_MARKERS:
            if fake in all_text:
                return {
                    "hallmark_detected": True,
                    "code":    fake,
                    "karat":   "Unknown",
                    "purity":  0,
                    "genuine": False,
                    "risk":    "High",
                    "raw_text": all_text[:80],
                }

        # No hallmark found — medium risk
        return {
            "hallmark_detected": False,
            "code":    "None",
            "karat":   "Unverified",
            "purity":  0,
            "genuine": False,
            "risk":    "Medium",
            "raw_text": all_text[:80],
        }

    except Exception as e:
        return {
            "hallmark_detected": False,
            "code":    "Error",
            "karat":   "Unknown",
            "purity":  0,
            "genuine": False,
            "risk":    "Medium",
            "error":   str(e),
        }
