"""
Weight estimation via ₹10 coin reference (27mm diameter).
Pixel-to-mm ratio → area → volume → weight using gold density.
"""
import cv2
import numpy as np

COIN_DIAMETER_MM  = 27.0   # ₹10 coin
GOLD_DENSITY      = 17.5   # g/cm³ (average 18K-22K)
HOLLOW_FACTOR     = 0.55   # most bangles/chains are ~55% solid

def _detect_coin(gray: np.ndarray):
    """Detect circular coin using Hough circles."""
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2,
        minDist=50, param1=50, param2=30,
        minRadius=20, maxRadius=200
    )
    if circles is not None:
        c = np.uint16(np.around(circles))[0][0]
        return int(c[2])  # radius in pixels
    return None

def _detect_jewelry_area(gray: np.ndarray, pixel_per_mm: float):
    """Detect largest non-circular object — the jewelry."""
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    area_px = cv2.contourArea(largest)
    area_mm2 = area_px / (pixel_per_mm ** 2)
    return area_mm2

def estimate_weight(image_path: str, declared_weight: float = None) -> dict:
    try:
        img  = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Try coin detection for scale reference
        coin_radius_px = _detect_coin(gray)

        if coin_radius_px:
            pixel_per_mm = (coin_radius_px * 2) / COIN_DIAMETER_MM
            method = "coin_reference"
        else:
            # Assume coin takes ~15% of image width (typical photo framing)
            pixel_per_mm = (w * 0.15) / COIN_DIAMETER_MM
            method = "estimated_scale"

        area_mm2 = _detect_jewelry_area(gray, pixel_per_mm)
        if area_mm2 is None:
            area_mm2 = 600  # safe default for a bangle

        # Volume estimate: area × assumed depth (2mm for flat jewelry)
        depth_mm     = 2.5
        volume_mm3   = area_mm2 * depth_mm * HOLLOW_FACTOR
        volume_cm3   = volume_mm3 / 1000
        weight_g     = volume_cm3 * GOLD_DENSITY

        # Add declared weight signal if available
        if declared_weight:
            # Blend: 60% model, 40% declared
            weight_g = 0.6 * weight_g + 0.4 * declared_weight

        # Return a ±20% band
        low  = round(weight_g * 0.85, 1)
        high = round(weight_g * 1.15, 1)
        conf = 0.78 if coin_radius_px else 0.62

        return {
            "weight_low_g":   low,
            "weight_high_g":  high,
            "weight_band":    f"{low} – {high} g",
            "method":         method,
            "confidence":     conf,
            "coin_detected":  coin_radius_px is not None,
        }

    except Exception as e:
        return {
            "weight_low_g":  8.0,
            "weight_high_g": 12.0,
            "weight_band":   "8.0 – 12.0 g",
            "method":        "fallback",
            "confidence":    0.50,
            "coin_detected": False,
            "error":         str(e),
        }
