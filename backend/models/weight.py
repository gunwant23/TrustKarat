import math

PIXEL_TO_CM = 0.026
GOLD_DENSITY = 19.3

FILL_FACTORS = {
    "FINGER RING": 0.6, "BANGLE": 0.5, "BRACELET": 0.4,
    "CHAIN": 0.25, "NECKLACE": 0.35, "PENDANT": 0.35,
    "EAR WEAR": 0.15, "NOSE SCREW": 0.1, "ARMBELT": 0.5,
    "VODIYANAM": 0.6, "24 KT COIN": 0.95
}

def estimate_weight(img_path: str, declared_weight: float = None, detection: dict = None) -> dict:

    # If we have detection bounding box, use notebook logic
    if detection and detection.get("width") and detection.get("height"):
        label = detection.get("type", "").upper()
        width_px = detection["width"]
        height_px = detection["height"]

        width_cm = width_px * PIXEL_TO_CM
        height_cm = height_px * PIXEL_TO_CM
        fill = FILL_FACTORS.get(label, 0.3)
        volume = 0

        if label in ["FINGER RING", "BANGLE"]:
            r = width_cm / 2
            thickness = 0.2 if label == "FINGER RING" else 0.4
            volume = 2 * math.pi * r * (thickness ** 2)

        elif label in ["CHAIN", "BRACELET"]:
            length_factor = 3 if label == "CHAIN" else 2
            thickness = 0.1 if label == "CHAIN" else 0.3
            volume = (width_cm * length_factor) * (thickness ** 2)

        elif label == "24 KT COIN":
            r = width_cm / 2
            volume = math.pi * r**2 * 0.2

        elif label in ["PENDANT", "EAR WEAR", "NOSE SCREW"]:
            thickness_map = {"PENDANT": 0.25, "EAR WEAR": 0.2, "NOSE SCREW": 0.1}
            volume = width_cm * height_cm * thickness_map.get(label, 0.2)

        elif label in ["ARMBELT", "VODIYANAM"]:
            thickness = 0.5 if label == "ARMBELT" else 0.6
            volume = (width_cm * 2.5) * (thickness ** 2)

        elif label == "NECKLACE":
            aspect_ratio = height_cm / width_cm if width_cm else 1
            if aspect_ratio < 0.5:
                volume = (width_cm * 2.5) * (0.2 ** 2)
                fill = 0.3
            else:
                volume = width_cm * height_cm * 0.4
                fill = 0.4
        else:
            volume = width_cm * height_cm * 0.2

        volume *= fill
        weight = volume * GOLD_DENSITY
        if weight > 200:
            weight = weight * 0.4

        return {"estimated_weight_g": round(weight, 2), "source": "vision"}

    # Fallback to declared weight
    if declared_weight:
        return {"estimated_weight_g": declared_weight, "source": "declared"}

    return {"estimated_weight_g": None, "source": "unknown"}
