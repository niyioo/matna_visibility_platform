import { useEffect, useState } from "react";
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

function useDebounced(value, delay = 400) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

export default function AnalyticsPage() {
  const { periods, thresholds, limits, today, refreshMs } = usePlatformConfig();
  const [period, setPeriod] = useState("weekly");
  const [range, setRange] = useState({ start: "", end: "" });
  const debouncedRange = useDebounced(range);

  const custom = Boolean(debouncedRange.start || debouncedRange.end);
  const rangeError =
    range.start && range.end && range.start > range.end ? "Start date must be on or before the end date." : "";

  const { data, loading, error, updatedAt, reload } = useApiData(
    ({ signal }) => {
      const params = custom
        ? { start_date: debouncedRange.start, end_date: debouncedRange.end }
        : { period };
      return Promise.all([
        analyticsApi.getSummary(custom ? { period: "daily", ...params } : params, { signal }),
        analyticsApi.getTrends(params, { signal }),
      ]);
    },
    [period, debouncedRange.start, debouncedRange.end, custom],
    { fallbackError: "Failed to load analytics.", refreshMs }
  );

  const [summary, trends] = data ?? [null, null];
  const series = trends?.series ?? [];
  const cmp = summary?.comparison ?? {};
  const prevLabel = summary?.previous
    ? `vs ${formatDate(summary.previous.start_date)} – ${formatDate(summary.previous.end_date)}`
    : "";

  return (
    <div>
      <div className="page-toolbar">
        <PageHeader title="Analytics" subtitle="Production efficiency, throughput and downtime — compared with the previous period." />
        <LiveStatus updatedAt={updatedAt} refreshMs={refreshMs} loading={loading} error={error} onRefresh={reload} />
      </div>

      <div className="filter-bar" role="search">
        <div className="form-group">
          <label htmlFor="an-period">Period</label>
          <select id="an-period" value={period} onChange={(e) => setPeriod(e.target.value)} disabled={custom}>
            {periods.map((p) => <option key={p.value} value={p.value} title={p.description}>{p.label}</option>)}
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="an-start">From</label>
          <input id="an-start" type="date" value={range.start} max={range.end || today}
            onChange={(e) => setRange((r) => ({ ...r, start: e.target.value }))} />
        </div>
        <div className="form-group">
          <label htmlFor="an-end">To</label>
          <input id="an-end" type="date" value={range.end} min={range.start || undefined} max={today}
            onChange={(e) => setRange((r) => ({ ...r, end: e.target.value }))} />
        </div>
        <div className="actions-row">
          {custom && (
            <button className="btn btn-ghost btn-sm" onClick={() => setRange({ start: "", end: "" })}>Clear dates</button>
          )}
        </div>
      </div>

      {rangeError && <div className="alert warning" role="alert" style={{ marginBottom: "var(--space-4)" }}>{rangeError}</div>}
      {error && !rangeError && <div className="alert error" role="alert" style={{ marginBottom: "var(--space-4)" }}>{error}</div>}

      {loading && !data ? (
        <Loader text="Loading analytics…" />
      ) : (
        <div aria-busy={loading} style={{ opacity: loading ? 0.6 : 1, transition: "opacity var(--transition-base)" }}>
          {summary && (
            <>
              <h2 className="section-title">
                {formatDate(summary.start_date)} – {formatDate(summary.end_date)}
                <span className="muted-small"> · {summary.entries_count} production day{summary.entries_count === 1 ? "" : "s"}</span>
              </h2>
              <div className="kpi-grid">
                <KpiCard label="Total inflow" value={formatNumber(summary.total_inflow)} suffix="t" comparison={cmp.total_inflow} comparisonLabel={prevLabel} />
                <KpiCard label="Total output" value={formatNumber(summary.total_output)} suffix="t" comparison={cmp.total_output} comparisonLabel={prevLabel} />
                <KpiCard
                  label="Weighted yield"
                  value={formatNumber(summary.yield_percent)}
                  suffix="%"
                  comparison={cmp.yield_percent}
                  comparisonLabel={prevLabel}
                  hint="Total output ÷ total inflow"
                />
                <KpiCard label="Total downtime" value={formatNumber(summary.total_downtime, 0)} suffix="min" comparison={cmp.total_downtime} comparisonLabel={prevLabel} />
                <KpiCard label="Avg downtime / day" value={formatNumber(summary.average_downtime, 0)} suffix="min" comparison={cmp.average_downtime} comparisonLabel={prevLabel} />
              </div>
            </>
          )}

          <div className="charts-grid">
            <YieldTrendChart data={series} target={trends?.stats?.yield_target} />
            <InflowOutputChart data={series} />
            <DowntimeTrendChart data={series} />
            {trends?.stats?.yield_mean != null && (
              <section className="chart-card stats-card" aria-label="Variability">
                <div className="chart-card-header"><h4>Variability</h4></div>
                <dl className="stats-list">
                  <div><dt>Mean daily yield</dt><dd>{formatNumber(trends.stats.yield_mean)}%</dd></div>
                  <div><dt>Yield std. deviation</dt><dd>± {formatNumber(trends.stats.yield_std)} pts</dd></div>
                  <div><dt>Mean daily downtime</dt><dd>{formatNumber(trends.stats.downtime_mean, 0)} min</dd></div>
                  <div><dt>Unusual days flagged</dt><dd>{series.filter((d) => d.yield_anomaly || d.downtime_anomaly).length}</dd></div>
                </dl>
                {thresholds && (
                  <p className="muted-small">
                    Red points are days more than {thresholds.anomaly_sigma}σ from the period mean.
                    {limits && ` Maximum range: ${limits.max_range_days} days.`}
                  </p>
                )}
              </section>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
