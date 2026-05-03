import easyocr

reader = easyocr.Reader(['en'])

HALLMARK_KEYWORDS = ["916", "750", "585", "22K", "18K", "14K", "BIS"]

def read_hallmark(img_path: str) -> dict:
    results = reader.readtext(img_path)

    for (bbox, text, prob) in results:
        for key in HALLMARK_KEYWORDS:
            if key in text.upper():
                return {
                    "karat_code": text,
                    "confidence": round(prob, 2),
                    "fraud_flag": False
                }

    return {
        "karat_code": None,
        "confidence": 0.0,
        "fraud_flag": True
    }
