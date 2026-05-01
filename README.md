# TrustKarat — Build & Run Guide

## Project Structure
```
trustkarat/
├── backend/
│   ├── main.py              ← FastAPI server (entry point)
│   ├── requirements.txt     ← Python dependencies
│   └── models/
│       ├── detector.py      ← YOLOv8n jewelry detection
│       ├── ocr.py           ← EasyOCR hallmark reading
│       ├── audio.py         ← librosa MFCC + SVM tap test
│       ├── weight.py        ← Coin-reference weight estimation
│       └── decision.py      ← XGBoost loan decision
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── index.css
        └── screens/
            ├── Home.jsx + .module.css
            ├── Capture.jsx + .module.css
            ├── AudioTest.jsx + .module.css
            ├── Loading.jsx + .module.css
            └── Results.jsx + .module.css
```

---

## DAY 1 — Setup & Backend Live

### P1 (ML) + P2 (Backend): Do this together

```bash
# 1. Clone / unzip the project
cd trustkarat/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies  (~5 min, downloads models)
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. Test it works — open browser:
# http://localhost:8000
# Should show: {"status": "TrustKarat API live"}
```

### P3 (Frontend): Do this in parallel

```bash
cd trustkarat/frontend

# 1. Install
npm install

# 2. Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# 3. Run
npm run dev

# 4. Open on phone:
# Find your laptop IP: ipconfig (Windows) or ifconfig (Mac)
# Open http://YOUR_IP:5173 on phone
```

**End of Day 1 goal:** Open the app on your phone → tap Start → camera opens → take photo → audio screen appears.

---

## DAY 2 — Connect & Test Real Models

### First API test (P2 runs this)
```bash
# Test the assess endpoint with a real image
curl -X POST http://localhost:8000/assess \
  -F "image=@test_gold.jpg" \
  | python -m json.tool
```

### Expected response shape:
```json
{
  "decision": "Pre-Approved",
  "decision_color": "green",
  "message": "Gold assessment passed. Proceed to custody collection.",
  "risk_level": "Low",
  "confidence": "78%",
  "jewelry_type": "bangle",
  "hallmark_code": "916",
  "hallmark_genuine": true,
  "karat_band": "22K",
  "weight_band": "9.5 – 12.0 g",
  "audio_purity": "22K",
  "fraud_flags": "None",
  "scores": {
    "hallmark": 90,
    "detection": 72,
    "weight": 80,
    "audio": 90
  }
}
```

### Connect frontend to real backend (P3)
Update `.env`:
```
VITE_API_URL=http://YOUR_LAPTOP_IP:8000
```

---

## DAY 3 — Deploy & Wrap APK

### Deploy Backend to Render (free, 10 min)

1. Push `backend/` folder to a GitHub repo
2. Go to render.com → New → Web Service
3. Connect GitHub repo
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`
5. Copy the live URL (e.g. `https://trustkarat-api.onrender.com`)

### Deploy Frontend to Vercel (free, 5 min)

1. Push `frontend/` to GitHub
2. Go to vercel.com → New Project → Import repo
3. Add Environment Variable:
   - `VITE_API_URL` = `https://trustkarat-api.onrender.com`
4. Deploy → get URL like `https://trustkarat.vercel.app`

### Wrap as APK using PWABuilder (free, zero code)

1. Open https://www.pwabuilder.com
2. Enter your Vercel URL
3. Click Build → Android → Download
4. You get a signed `.apk` file — submit this to judges

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Camera not opening | Must use HTTPS or localhost — Vercel gives HTTPS automatically |
| CORS error | Backend has CORS open for all origins — restart server |
| YOLOv8 slow first run | Downloads weights once (~6MB) — subsequent runs are fast |
| EasyOCR slow first run | Downloads language model once (~100MB) — expected |
| Audio not recording | Browser requires HTTPS for microphone — use Vercel URL |

---

## Quick demo script (for judges)

1. Open app → tap **Start Assessment**
2. Photograph a gold ring/bangle → tap **Use This Photo**
3. Screen shows tap test → tap **Ready** → drop the jewelry → it records
4. Loading screen shows AI steps (5 seconds)
5. Results screen shows: jewelry type, weight band, purity, hallmark code, risk level, loan offer

**Key things to say:**
- "We use YOLOv8n for jewelry detection, EasyOCR for hallmark reading, and librosa MFCC for audio purity analysis — all running on our FastAPI server"
- "The ₹10 coin in the frame is our scale reference for weight estimation"
- "XGBoost fuses all signals into the final loan decision"
- "All models export to ONNX/TFLite — ready for on-device inference"
>>>>>>> b55bdfe (Basic Commit)
