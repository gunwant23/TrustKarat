import styles from "./Home.module.css";

export default function Home({ onStart }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.top}>
        <div className={styles.logo}>TrustKarat</div>
        <div className={styles.tagline}>Less waiting, more weighting.</div>
      </div>

      <div className={styles.mid}>
        <div className={styles.stat}>
          <span className={styles.statVal}>₹10L Cr+</span>
          <span className={styles.statLbl}>gold loan market</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statVal}>2 min</span>
          <span className={styles.statLbl}>to pre-qualify</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statVal}>0</span>
          <span className={styles.statLbl}>branch visits</span>
        </div>
      </div>

      <div className={styles.steps}>
        {[
          { icon: "📷", txt: "Scan your jewelry" },
          { icon: "🔊", txt: "Do the tap test" },
          { icon: "✅", txt: "Get your loan offer" },
        ].map((s, i) => (
          <div key={i} className={styles.step}>
            <span className={styles.stepIcon}>{s.icon}</span>
            <span className={styles.stepTxt}>{s.txt}</span>
          </div>
        ))}
      </div>

      <button className={styles.cta} onClick={onStart}>
        Start Assessment →
      </button>

      <p className={styles.note}>
        No branch visit · No XRF machine · Just your phone
      </p>
    </div>
  );
}
