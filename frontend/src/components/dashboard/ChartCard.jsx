import EmptyState from "../common/EmptyState";

export const axisProps = {
  tick: { fontSize: 11, fill: "var(--text-muted)" },
  tickLine: false,
  axisLine: false,
};

/** "2026-03-18" → "18 Mar" without timezone shifts. */
export const shortDate = (value) => {
  if (typeof value !== "string") return value;
  const [y, m, d] = value.split("-").map(Number);
  if (!y || !m || !d) return value;
  return new Date(y, m - 1, d).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
};

export function ChartTooltip({ active, payload, label, format }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload ?? {};
  const anomaly = row.yield_anomaly || row.downtime_anomaly;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-label">{shortDate(label)}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {format(p.value)}
        </p>
      ))}
      {anomaly && <p className="chart-tooltip-flag">⚠ Outside normal range</p>}
    </div>
  );
}

/** Red dot for points the backend flagged as anomalous; default dot otherwise. */
export const anomalyDot = (flag, color) => function AnomalyDot({ cx, cy, payload, index }) {
  if (cx == null || cy == null) return null;
  const isAnomaly = Boolean(payload?.[flag]);
  return (
    <circle
      key={`dot-${index}`}
      cx={cx}
      cy={cy}
      r={isAnomaly ? 5 : 3}
      fill={isAnomaly ? "var(--kpi-rose)" : color}
      stroke={isAnomaly ? "var(--panel)" : "none"}
      strokeWidth={isAnomaly ? 2 : 0}
    />
  );
};

export default function ChartCard({ title, meta, empty, children }) {
  return (
    <section className="chart-card" aria-label={title}>
      <div className="chart-card-header">
        <h4>{title}</h4>
        {meta && <span>{meta}</span>}
      </div>
      <div className="chart-box">
        {empty ? <EmptyState title="No data for this period" /> : children}
      </div>
    </section>
  );
}
