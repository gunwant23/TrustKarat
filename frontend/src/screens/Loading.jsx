import styles from "./Loading.module.css";
import { useEffect, useState } from "react";

const STEPS = [
  "Detecting jewelry type…",
  "Reading hallmark stamp…",
  "Estimating weight…",
  "Analysing audio purity…",
  "Computing risk score…",
];

export default function Loading() {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const iv = setInterval(() => setIdx(i => Math.min(i + 1, STEPS.length - 1)), 2200);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className={styles.wrap}>
      <div className={styles.logo}>TrustKarat</div>
      <div className={styles.spinner}>
        <div className={styles.ring} />
        <span className={styles.ringIcon}>💍</span>
      </div>
      <p className={styles.step}>{STEPS[idx]}</p>
      <div className={styles.dots}>
        {STEPS.map((_, i) => (
          <div key={i} className={`${styles.dot} ${i <= idx ? styles.active : ""}`} />
        ))}
      </div>
    </div>
  );
}
