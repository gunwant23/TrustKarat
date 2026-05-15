# TrustKarat — AI-Powered Gold Jewelry Assessment

> Pre-screen gold jewelry for loan approval using computer vision, audio analysis, and NLP — before physical branch visit.

**Live Demo:** [https://trustkarat.vercel.app](https://trust-karat.vercel.app/)  
**Backend API:** https://guns23-trustkarat-api.hf.space  
**Docs:** https://guns23-trustkarat-api.hf.space/docs

---

## Overview

TrustKarat is a full-stack AI application that helps NBFCs (Non-Banking Financial Companies) pre-assess gold jewelry for loan eligibility. A field agent photographs the jewelry, optionally records a tap sound, and receives an instant AI-generated assessment — reducing branch visit time and fraud risk.

### Pipeline

```
Photo → Jewelry Detection → Hallmark OCR → Weight Estimation
                                                    ↓
Audio Tap → Purity Classification (SVM)    Decision Engine
                                                    ↓
Text Description → NLP Feature Extraction → Loan Pre-Approval / Reject
```

---

## Features

- **Jewelry Detection** — MobileNetV2 classifier (necklace, ring) with shape-based heuristic fallback for low-confidence predictions
- **Hallmark OCR** — EasyOCR reads BIS hallmark codes (916, 750, 585, 22K, 18K, 14K)
- **Weight Estimation** — Bounding box dimensions × gold density formula per jewelry type
- **Audio Tap Test** — MFCC feature extraction → SVM classifier (14K / 22K / 24K purity)
- **NLP Text Analysis** — Parses agent description for karat mentions, brand trust, age signals, fraud keywords
- **Decision Engine** — Weighted scoring (Detection 40%, Audio 30%, Hallmark 20%, Weight 10%) with practical warnings
- **Live Gold Price** — Fetches real-time gold price and computes provisional loan offer (75% LTV per RBI guidelines)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite, CSS Modules |
| Backend | FastAPI + Uvicorn |
| Jewelry Detection | MobileNetV2 (PyTorch) + shape heuristics |
| Hallmark OCR | EasyOCR |
| Audio Purity | librosa MFCC + SVM (scikit-learn) |
| NLP | Custom rule-based feature extractor |
| Deployment | Hugging Face Spaces (Docker) + Vercel |

---

## Project Structure

```
TrustKarat/
├── backend/
│   ├── main.py                  ← FastAPI server, /assess endpoint
│   ├── Dockerfile               ← HF Spaces deployment
│   ├── requirements.txt
│   └── models/
│       ├── detector.py          ← MobileNetV2 + heuristic fallback
│       ├── ocr.py               ← EasyOCR hallmark reader
│       ├── audio.py             ← SVM tap-test purity classifier
│       ├── weight.py            ← Bounding box weight estimation
│       ├── decision.py          ← Weighted scoring + loan decision
│       ├── text_features.py     ← NLP feature extraction & fusion
│       ├── jewelry_classifier.pkl  ← Trained MobileNetV2 weights
│       ├── svm_purity.pkl       ← Trained SVM for audio purity
│       ├── scaler.pkl           ← Feature scaler for SVM
│       └── label_encoder.pkl    ← Label encoder for SVM output
└── frontend/
    ├── src/
    │   ├── App.jsx              ← Screen router
    │   └── screens/
    │       ├── Home.jsx
    │       ├── Capture.jsx      ← Photo + description input
    │       ├── AudioTest.jsx    ← 10-second tap recording
    │       ├── Loading.jsx
    │       ├── GoldEstimate.jsx ← Live gold price + loan offer
    │       └── Results.jsx      ← Full assessment report
    ├── .env                     ← VITE_API_URL
    └── vite.config.js
```

---

## API

### `POST /assess`

| Field | Type | Required |
|---|---|---|
| `image` | File | ✅ |
| `audio` | File | ❌ |
| `declared_weight` | Float | ❌ |
| `description` | String | ❌ |

**Response:**
```json
{
  "decision": "Pre-Approved",
  "decision_color": "green",
  "message": "Assessment passed. Verify weight physically before final approval.",
  "warnings": ["⚠ Audio tap test skipped — purity unverified"],
  "risk_level": "Low",
  "confidence": "74%",
  "jewelry_type": "necklace",
  "hallmark_code": "916",
  "hallmark_genuine": true,
  "karat_band": "22K",
  "weight_band": "17.6g",
  "audio_purity": "Not tested",
  "fraud_flags": "None",
  "scores": {
    "hallmark": 90,
    "detection": 72,
    "weight": 80,
    "audio": 65
  }
}
```

### `GET /health`
```json
{"status": "ok"}
```

---

## Local Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
# Create .env file:
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

Open **http://localhost:5173**

---

## Deployment

### Backend — Hugging Face Spaces (Docker)
```bash
# Push models/ and main.py to HF Space repo
git remote add hf https://huggingface.co/spaces/Guns23/trustkarat-api
git push hf main
```

### Frontend — Vercel
```
Root Directory : frontend
Build Command  : npm run build
Output Dir     : dist
Env Var        : VITE_API_URL = https://guns23-trustkarat-api.hf.space
```

---

## Decision Logic

| Score | Decision |
|---|---|
| ≥ 75 + hallmark + audio | Pre-Approved ✅ |
| ≥ 72 + hallmark | Pre-Approved ✅ |
| 60 – 72 | Needs Verification ⚠ |
| 50 – 60 | Needs Verification ⚠ |
| 35 – 50 | Reject ❌ |
| < 35 | Reject ❌ |

**Scoring weights:** Detection 40% · Audio 30% · Hallmark 20% · Weight 10%  
**Text blend:** Final = model score × 85% + text score × 15%  
**Loan offer:** 75% of estimated gold value (RBI LTV guideline)

---

## Known Limitations

- Jewelry classifier trained only on necklace and ring — other types use shape heuristics
- Weight estimation based on pixel dimensions, not physical scale
- Audio purity requires quiet environment for accurate recording
- No user authentication (prototype only)
- Gold price fetched from free API — may have brief delays

---

## License

MIT License — open for research and educational use.
