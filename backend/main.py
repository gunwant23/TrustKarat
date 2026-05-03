from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn, tempfile, os, shutil

from models.detector   import detect_jewelry
from models.ocr        import read_hallmark
from models.audio      import analyse_audio
from models.weight     import estimate_weight
from models.decision   import make_decision

app = FastAPI(title="TrustKarat API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "TrustKarat API live"}

@app.post("/assess")
async def assess(
    image: UploadFile = File(...),
    audio: UploadFile = File(None),
    declared_weight: float = Form(None),
):
    # ── Save uploaded files to temp ─────────────────────────
    tmp_dir = tempfile.mkdtemp()
    img_path = os.path.join(tmp_dir, "jewelry.jpg")
    with open(img_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    audio_path = None
    if audio:
        audio_path = os.path.join(tmp_dir, "tap.wav")
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio.file, f)

    # ── Run models ───────────────────────────────────────────
    detection   = detect_jewelry(img_path)        # type + confidence
    hallmark    = read_hallmark(img_path)          # karat code + fraud flag
    weight_est = estimate_weight(img_path, declared_weight, detection)  # weight band
    audio_res   = analyse_audio(audio_path)        # purity class

    # ── Fuse into final decision ─────────────────────────────
    result = make_decision(detection, hallmark, weight_est, audio_res)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return JSONResponse(content={
    # Fields Results.jsx expects
    "decision":         fused["decision"],
    "risk_level":       "Low" if fused["final_score"] >= 72 else "Medium" if fused["final_score"] >= 50 else "High",
    "message":          "Gold assessment complete.",
    "jewelry_type":     detection.get("type", "Unknown"),
    "weight_band":      f"{weight_est.get('estimated_weight_g', '?')}g ({weight_est.get('source', '')})",
    "karat_band":       hallmark.get("karat_code") or text_explanation.get("karat_from_text", "Unknown"),
    "hallmark_code":    hallmark.get("karat_code", "None"),
    "hallmark_genuine": not hallmark.get("fraud_flag", True),
    "audio_purity":     audio_res.get("purity_class", "N/A") if audio_res else "N/A",
    "fraud_flags":      ", ".join(text_explanation.get("signals_detected", [])) or "None",
    "confidence":       f"{fused['final_score']}%",
    "scores": {
        "hallmark": fused["score_breakdown"]["hallmark_score"],
        "visual":   fused["score_breakdown"]["visual_score"],
        "audio":    fused["score_breakdown"]["audio_score"],
        "text":     fused["score_breakdown"]["text_score"],
        "weight":   fused["score_breakdown"]["weight_score"],
    },
    # Extra data
    "text_analysis": text_explanation,
})
