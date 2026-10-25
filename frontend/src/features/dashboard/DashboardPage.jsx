import { analyticsApi } from "../../api/analyticsApi";
import KpiCard from "../../components/common/KpiCard";
import Loader from "../../components/common/Loader";
import PageHeader from "../../components/common/PageHeader";
import DowntimeTrendChart from "../../components/dashboard/DowntimeTrendChart";
import InflowOutputChart from "../../components/dashboard/InflowOutputChart";
import YieldTrendChart from "../../components/dashboard/YieldTrendChart";
import LiveStatus from "../../components/common/LiveStatus";
import useApiData from "../../hooks/useApiData";
import usePlatformConfig from "../../hooks/usePlatformConfig";
import { formatDate, formatNumber } from "../../utils/formatters";

const Svg = ({ d }) => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>
);

const ICONS = {
  inflow: "M12 2l9 7H3l9-7zM3 9v13h18V9",
  output: "M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z",
  yield: "M18 20V10 M12 20V4 M6 20v-6",
  downtime: "M12 22c5.52 0 10-4.48 10-10S17.52 2 12 2 2 6.48 2 12s4.48 10 10 10z M12 6v6l4 2",
  stock: "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z",
  starch: "M22 12h-4l-3 9L9 3l-3 9H2",
};

const HEALTH = {
  healthy: { label: "Operations healthy", tone: "success", text: "All monitored KPIs are within their thresholds." },
  attention: { label: "Needs attention", tone: "warning", text: "One or more KPIs are outside their target range." },
  critical: { label: "Critical", tone: "error", text: "Immediate action is recommended on the alerts below." },
};

function AlertList({ alerts }) {
  if (!alerts?.length) return null;
  return (
    <section className="card" aria-label="Operational alerts" style={{ marginBottom: "var(--space-6)" }}>
      <div className="card-header"><h3>Operational alerts</h3></div>
      <ul className="alert-list">
        {alerts.map((a) => (
          <li key={a.code} className={`alert-item ${a.severity}`}>
            <span className={`badge ${a.severity === "critical" ? "badge-red" : a.severity === "warning" ? "badge-amber" : "badge-blue"}`}>
              {a.severity}
            </span>
            <div>
              <strong>{a.title}</strong>
              <p>{a.message}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

const daySpan = (start, end) => {
  if (!start || !end) return null;
  const [a, b] = [start, end].map((d) => new Date(`${d}T00:00:00`));
  return Math.round((b - a) / 86400000) + 1;
};

export default function DashboardPage() {
  const { refreshMs } = usePlatformConfig();
  const { data: dash, loading, error, updatedAt, reload } = useApiData(
    ({ signal }) => analyticsApi.getDashboard({ signal }),
    [],
    { fallbackError: "Failed to load dashboard data.", refreshMs }
  );

  if (loading && !dash) return <Loader text="Loading dashboard…" />;

  const trends = dash?.trends;
  const series = trends?.series ?? [];
  const week = dash?.week;
  const health = HEALTH[dash?.health] ?? null;
  const cover = dash?.raw_stock_cover_days;
  const weekDays = daySpan(week?.start_date, week?.end_date);
  const trendDays = daySpan(trends?.start_date, trends?.end_date);

  return (
    <div>
      <div className="page-toolbar">
        <PageHeader
          title="Operational Dashboard"
          subtitle={dash?.snapshot_date
            ? `Latest production day: ${formatDate(dash.snapshot_date)}`
            : "No production data recorded yet."}
        />
        <LiveStatus updatedAt={updatedAt} refreshMs={refreshMs} loading={loading} error={error} onRefresh={reload} />
      </div>

      {error && <div className="alert error" role="alert" style={{ marginBottom: "var(--space-5)" }}>{error}</div>}

      {health && (
        <div className={`health-banner ${health.tone}`} role="status">
          <span className="health-dot" aria-hidden="true" />
          <strong>{health.label}</strong>
          <span>{health.text}</span>
        </div>
      )}

      <h2 className="section-title">Latest production day</h2>
      <div className="kpi-grid">
        <KpiCard label="Cassava inflow" value={formatNumber(dash?.latest_inflow)} suffix="t" icon={<Svg d={ICONS.inflow} />} iconColor="var(--kpi-blue)" />
        <KpiCard label="Starch output" value={formatNumber(dash?.latest_output)} suffix="t" icon={<Svg d={ICONS.output} />} iconColor="var(--kpi-teal)" />
        <KpiCard
          label="Yield"
          value={formatNumber(dash?.latest_yield)}
          suffix="%"
          icon={<Svg d={ICONS.yield} />}
          iconColor="var(--kpi-green)"
          hint={dash?.thresholds ? `Target ${dash.thresholds.yield_target}% · critical below ${dash.thresholds.yield_critical}%` : undefined}
        />
        <KpiCard label="Downtime" value={formatNumber(dash?.latest_downtime, 0)} suffix="min" icon={<Svg d={ICONS.downtime} />} iconColor="var(--kpi-amber)" />
        <KpiCard
          label="Raw cassava stock"
          value={formatNumber(dash?.raw_cassava_stock)}
          suffix="t"
          icon={<Svg d={ICONS.stock} />}
          iconColor="var(--kpi-purple)"
          hint={cover != null ? `≈ ${formatNumber(cover, 1)} days of production` : undefined}
        />
        <KpiCard label="Finished starch stock" value={formatNumber(dash?.finished_starch_stock)} suffix="t" icon={<Svg d={ICONS.starch} />} iconColor="var(--kpi-rose)" />
      </div>

      <AlertList alerts={dash?.alerts?.filter((a) => a.code !== "NO_DATA")} />

      {week && (
        <>
          <h2 className="section-title">
            Last {weekDays} days <span className="muted-small">({formatDate(week.start_date)} – {formatDate(week.end_date)}) vs the {weekDays} days before</span>
          </h2>
          <div className="kpi-grid">
            <KpiCard label="Total inflow" value={formatNumber(week.summary.total_inflow)} suffix="t" comparison={week.comparison.total_inflow} comparisonLabel="" />
            <KpiCard label="Total output" value={formatNumber(week.summary.total_output)} suffix="t" comparison={week.comparison.total_output} comparisonLabel="" />
            <KpiCard label="Weighted yield" value={formatNumber(week.summary.yield_percent)} suffix="%" comparison={week.comparison.yield_percent} comparisonLabel="" />
            <KpiCard label="Total downtime" value={formatNumber(week.summary.total_downtime, 0)} suffix="min" comparison={week.comparison.total_downtime} comparisonLabel="" />
          </div>
        </>
      )}

      <h2 className="section-title">
        Last {trendDays} days <span className="muted-small">({formatDate(trends?.start_date)} – {formatDate(trends?.end_date)})</span>
      </h2>
      <div className="charts-grid">
        <YieldTrendChart data={series} target={trends?.stats?.yield_target} />
        <InflowOutputChart data={series} />
        <DowntimeTrendChart data={series} />
      </div>
    </div>
  );
}
