
"""
detector.py — uses fine-tuned MobileNetV2 for necklace/ring classification
Drop jewelry_classifier_v2.pkl into models/ folder
"""
import pickle, os
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image

_PKL_PATH = os.path.join(os.path.dirname(__file__), "jewelry_classifier_v2.pkl")
_model    = None
_meta     = None

def _load():
    global _model, _meta
    with open(_PKL_PATH, "rb") as f:
        saved = pickle.load(f)

    _meta    = saved
    classes  = saved["classes"]
    img_size = saved.get("img_size", 224)

    m = models.mobilenet_v2(weights=None)
    in_features = m.classifier[1].in_features
    m.classifier = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, 256),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(256, len(classes))
    )
    m.load_state_dict(saved["model_state_dict"])
    m.eval()
    _model = m

_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

def detect_jewelry(img_path: str) -> dict:
    try:
        if _model is None:
            _load()

        img    = Image.open(img_path).convert("RGB")
        tensor = _tf(img).unsqueeze(0)

        with torch.no_grad():
            out   = _model(tensor)
            probs = torch.softmax(out, dim=1)[0].numpy()

        classes  = _meta["classes"]
        pred_idx = int(probs.argmax())
        pred_cls = classes[pred_idx]
        conf     = float(probs[pred_idx])

        return {
            "type":          pred_cls,
            "jewelry_type":  pred_cls,
            "confidence":    round(conf * 100, 2),
            "all_probs":     {cls: round(float(p)*100, 2) for cls, p in zip(classes, probs)},
            "width":         None,
            "height":        None,
        }
    except Exception as e:
        return {"type": "unknown", "jewelry_type": "unknown",
                "confidence": 0.0, "width": None, "height": None, "error": str(e)}
