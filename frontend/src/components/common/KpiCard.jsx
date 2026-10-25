import { memo } from "react";

/**
 * Metric card with an optional period comparison.
 *
 * `comparison` is the backend's { trend: "up"|"down"|"flat", change_percent, favourable }.
 * The arrow shows direction; the colour shows whether that direction is good
 * for the operation (e.g. downtime going down is green).
 */
function KpiCard({ label, value, suffix = "", icon, iconColor = "var(--brand-600)", comparison, comparisonLabel = "vs previous period", hint }) {
  let badge = null;
  if (comparison && comparison.previous != null) {
    const arrow = comparison.trend === "up" ? "↑" : comparison.trend === "down" ? "↓" : "→";
    const tone = comparison.favourable === true ? "up" : comparison.favourable === false ? "down" : "neutral";
    const pct = comparison.change_percent;
    const text = pct == null ? "new" : `${Math.abs(pct).toFixed(1)}%`;
    badge = (
      <span className={`kpi-badge ${tone}`} title={`Previous: ${comparison.previous}`}>
        {arrow} {text} <span className="kpi-badge-note">{comparisonLabel}</span>
      </span>
    );
  }

  return (
    <div className="kpi-card">
      <div className="kpi-card-top">
        <p className="kpi-label">{label}</p>
        {icon && (
          <div className="kpi-icon" style={{ background: `color-mix(in srgb, ${iconColor} 12%, transparent)`, color: iconColor }} aria-hidden="true">
            {icon}
          </div>
        )}
      </div>

      <div className="kpi-value-row">
        <span className="kpi-value">{value ?? "—"}</span>
        {suffix && value !== "—" && <span className="kpi-suffix">{suffix}</span>}
      </div>

      {badge}
      {hint && <span className="kpi-hint">{hint}</span>}
    </div>
  );
}

export default memo(KpiCard);
