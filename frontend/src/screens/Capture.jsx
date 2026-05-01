import { useRef, useState } from "react";
import styles from "./Capture.module.css";

export default function Capture({ onCapture, onBack }) {
  const videoRef   = useRef(null);
  const canvasRef  = useRef(null);
  const inputRef   = useRef(null);
  const [streaming, setStreaming] = useState(false);
  const [preview,   setPreview]   = useState(null);
  const [file,      setFile]      = useState(null);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: 1280, height: 720 }
      });
      videoRef.current.srcObject = stream;
      videoRef.current.play();
      setStreaming(true);
    } catch {
      // Fallback to upload if camera denied
      inputRef.current.click();
    }
  }

  function capture() {
    const canvas = canvasRef.current;
    const video  = videoRef.current;
    canvas.width  = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      const f = new File([blob], "jewelry.jpg", { type: "image/jpeg" });
      setFile(f);
      setPreview(URL.createObjectURL(blob));
      // Stop camera stream
      video.srcObject?.getTracks().forEach(t => t.stop());
      setStreaming(false);
    }, "image/jpeg", 0.92);
  }

  function handleUpload(e) {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  function retake() {
    setFile(null);
    setPreview(null);
    startCamera();
  }

  const tips = [
    "Place jewelry on a dark surface",
    "Include a ₹10 coin for scale",
    "Ensure hallmark stamp is visible",
    "Use good natural light",
  ];

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <button className={styles.back} onClick={onBack}>←</button>
        <span className={styles.title}>Scan Jewelry</span>
        <span className={styles.step}>1 / 2</span>
      </div>

      {!streaming && !preview && (
        <div className={styles.placeholder}>
          <div className={styles.frame}>
            <span className={styles.frameIcon}>💍</span>
            <span className={styles.frameHint}>Place jewelry in frame</span>
          </div>
          <div className={styles.tipBox}>
            {tips.map((t, i) => (
              <div key={i} className={styles.tip}>
                <span className={styles.tipDot} />
                {t}
              </div>
            ))}
          </div>
          <div className={styles.btnRow}>
            <button className={styles.btn} onClick={startCamera}>Open Camera</button>
            <button className={styles.btnOutline} onClick={() => inputRef.current.click()}>
              Upload Photo
            </button>
          </div>
        </div>
      )}

      {streaming && (
        <div className={styles.cameraWrap}>
          <video ref={videoRef} className={styles.video} playsInline muted />
          <div className={styles.overlay}>
            <div className={styles.corners} />
          </div>
          <p className={styles.camHint}>Ensure hallmark stamp is visible</p>
          <button className={styles.shutterBtn} onClick={capture}>
            <span className={styles.shutterInner} />
          </button>
        </div>
      )}

      {preview && (
        <div className={styles.previewWrap}>
          <img src={preview} alt="Jewelry preview" className={styles.preview} />
          <p className={styles.previewHint}>
            Make sure the hallmark stamp is visible in the photo
          </p>
          <div className={styles.btnRow}>
            <button className={styles.btnOutline} onClick={retake}>Retake</button>
            <button className={styles.btn} onClick={() => onCapture(file)}>
              Use This Photo →
            </button>
          </div>
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: "none" }} />
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        style={{ display: "none" }}
        onChange={handleUpload}
      />
    </div>
  );
}
