from inference_sdk import InferenceHTTPClient
import base64

client = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="osTGJSYBar9TeSoDQ3q9"
)

def detect_jewelry(img_path: str) -> dict:
    with open(img_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    result = client.infer(image_base64, model_id="jewellery-classifier/1")

    predictions = result.get("predictions", [])
    if not predictions:
        return {"type": "unknown", "confidence": 0.0}

    top = max(predictions, key=lambda x: x["confidence"])
    return {
        "type": top.get("class", "unknown"),
        "confidence": round(top["confidence"] * 100, 2)
    }
