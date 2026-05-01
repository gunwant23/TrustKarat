import styles from "./Results.module.css";

const COLOR = {
  "Pre-Approved":       "green",
  "Needs Verification": "orange",
  "Reject":             "red",
};

function Badge({ risk }) {
  const c = risk === "Low" ? "green" : risk === "Medium" ? "orange" : "red";
  return <span className={`${styles.badge} ${styles[c]}`}>{risk} Risk</span>;
}

function Row({ label, value, highlight }) {
  return (
    <div className={styles.row}>
      <span className={styles.rowLabel}>{label}</span>
      <span className={`${styles.rowValue} ${highlight ? styles[highlight] : ""}`}>
        {value}
      </span>
    </div>
  );
}

function ScoreBar({ label, score }) {
  return (
    <div className={styles.scoreRow}>
      <span className={styles.scoreLabel}>{label}</span>
      <div className={styles.barTrack}>
        <div className={styles.barFill} style={{ width: `${score}%` }} />
      </div>
      <span className={styles.scoreNum}>{score}</span>
    </div>
  );
}

export default function Results({ result, onReset }) {
  if (!result) return null;

  const decColor = COLOR[result.decision] || "orange";

  return (
    <div className={styles.wrap}>
      {/* Header */}
      <div className={styles.header}>
        <span className={styles.logo}>TrustKarat</span>
        <Badge risk={result.risk_level} />
      </div>

      {/* Decision banner */}
      <div className={`${styles.decision} ${styles[decColor]}`}>
        <span className={styles.decIcon}>
          {result.decision === "Pre-Approved" ? "✅" :
           result.decision === "Reject"       ? "❌" : "⚠️"}
        </span>
        <div>
          <div className={styles.decTitle}>{result.decision}</div>
          <div className={styles.decMsg}>{result.message}</div>
        </div>
      </div>

      {/* Assessment report */}
      <div className={styles.card}>
        <div className={styles.cardTitle}>Assessment Report</div>
        <Row label="Jewelry Type"  value={result.jewelry_type?.charAt(0).toUpperCase() + result.jewelry_type?.slice(1)} />
        <Row label="Weight Band"   value={result.weight_band} />
        <Row label="Purity Band"   value={result.karat_band} />
        <Row label="Hallmark"      value={result.hallmark_code}
             highlight={result.hallmark_genuine ? "green" : result.hallmark_code !== "None" ? "red" : null} />
        <Row label="Audio Purity"  value={result.audio_purity} />
        <Row label="Fraud Flags"   value={result.fraud_flags}
             highlight={result.fraud_flags === "None" ? "green" : "red"} />
        <div className={styles.divider} />
        <Row label="Confidence"    value={result.confidence} highlight="gold" />
      </div>

      {/* Score breakdown */}
      {result.scores && (
        <div className={styles.card}>
          <div className={styles.cardTitle}>Score Breakdown</div>
          {Object.entries(result.scores).map(([k, v]) => (
            <ScoreBar key={k} label={k.charAt(0).toUpperCase() + k.slice(1)} score={v} />
          ))}
        </div>
      )}

      {/* Action */}
      <div className={styles.actions}>
        {result.decision === "Pre-Approved" && (
          <div className={styles.loanBox}>
            <span className={styles.loanLabel}>Provisional Loan Offer</span>
            <span className={styles.loanAmt}>Up to ₹75,000</span>
            <span className={styles.loanNote}>Subject to physical custody verification</span>
          </div>
        )}
        <button className={styles.resetBtn} onClick={onReset}>
          Assess Another Item
        </button>
      </div>
    </div>
  );
}
