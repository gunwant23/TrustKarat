import { useState, useRef } from "react";
import styles from "./AudioTest.module.css";

export default function AudioTest({ onDone, onSkip, onBack }) {
  const [phase,      setPhase]      = useState("intro");  // intro | countdown | recording | done
  const [countdown,  setCountdown]  = useState(3);
  const [waveform,   setWaveform]   = useState([]);
  const mediaRecRef  = useRef(null);
  const chunksRef    = useRef([]);
  const animRef      = useRef(null);

  function startCountdown() {
    setPhase("countdown");
    let c = 3;
    setCountdown(c);
    const iv = setInterval(() => {
      c--;
      setCountdown(c);
      if (c === 0) {
        clearInterval(iv);
        startRecording();
      }
    }, 1000);
  }

  async function startRecording() {
    setPhase("recording");
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mr     = new MediaRecorder(stream, { mimeType: "audio/webm" });
    mediaRecRef.current  = mr;
    chunksRef.current    = [];

    mr.ondataavailable = (e) => chunksRef.current.push(e.data);
    mr.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      cancelAnimationFrame(animRef.current);
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      setPhase("done");
      onDone(blob);
    };

    // Fake waveform animation
    function animWave() {
      setWaveform(Array.from({ length: 24 }, () => Math.random() * 0.8 + 0.2));
      animRef.current = requestAnimationFrame(animWave);
    }
    animWave();

    mr.start();
    // Auto-stop after 3 seconds
    setTimeout(() => { if (mr.state === "recording") mr.stop(); }, 3000);
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <button className={styles.back} onClick={onBack}>←</button>
        <span className={styles.title}>Tap Test</span>
        <span className={styles.step}>2 / 2</span>
      </div>

      {phase === "intro" && (
        <div className={styles.body}>
          <div className={styles.icon}>🔊</div>
          <h2 className={styles.h2}>Audio Purity Test</h2>
          <p className={styles.desc}>
            Hold your jewelry 15 cm above a hard surface, then let it drop.
            We'll analyse the sound to estimate gold purity.
          </p>
          <div className={styles.steps}>
            {["Hold jewelry 15 cm high", "Let it drop onto the surface", "We record & analyse the tap sound"].map((t, i) => (
              <div key={i} className={styles.step2}>
                <span className={styles.stepNum}>{i + 1}</span>
                <span>{t}</span>
              </div>
            ))}
          </div>
          <button className={styles.btn} onClick={startCountdown}>
            Ready — Start Recording
          </button>
          <button className={styles.skip} onClick={onSkip}>
            Skip this step
          </button>
        </div>
      )}

      {phase === "countdown" && (
        <div className={styles.centered}>
          <div className={styles.countNum}>{countdown}</div>
          <p className={styles.countHint}>Get ready to drop…</p>
        </div>
      )}

      {phase === "recording" && (
        <div className={styles.centered}>
          <div className={styles.recLabel}>🔴  Recording</div>
          <div className={styles.wave}>
            {waveform.map((h, i) => (
              <div
                key={i}
                className={styles.bar}
                style={{ height: `${h * 60}px` }}
              />
            ))}
          </div>
          <p className={styles.recHint}>Drop the jewelry now…</p>
        </div>
      )}

      {phase === "done" && (
        <div className={styles.centered}>
          <div className={styles.doneIcon}>✅</div>
          <p className={styles.doneMsg}>Tap recorded! Analysing…</p>
        </div>
      )}
    </div>
  );
}
