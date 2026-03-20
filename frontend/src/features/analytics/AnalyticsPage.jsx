import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/common/Card";
import YieldTrendChart from "../../components/dashboard/YieldTrendChart";
import InflowOutputChart from "../../components/dashboard/InflowOutputChart";
import DowntimeTrendChart from "../../components/dashboard/DowntimeTrendChart";
import { analyticsApi } from "../../api/analyticsApi";
import { formatNumber } from "../../utils/formatters";

export default function AnalyticsPage() {
  const [period, setPeriod] = useState("weekly");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [summary, setSummary] = useState(null);
  const [yieldTrend, setYieldTrend] = useState([]);
  const [inflowOutput, setInflowOutput] = useState([]);
  const [downtimeTrend, setDowntimeTrend] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        setError("");

        const params = {
          start_date: startDate,
          end_date: endDate
        };

        const [summaryData, yieldData, inflowData, downtimeData] = await Promise.all([
          analyticsApi.getSummary(period, params),
          analyticsApi.getYieldTrend(params),
          analyticsApi.getInflowVsOutput(params),
          analyticsApi.getDowntimeTrend(params)
        ]);

        setSummary(summaryData);
        setYieldTrend(yieldData);
        setInflowOutput(inflowData);
        setDowntimeTrend(downtimeData);
      } catch (err) {
        console.error(err);
        setError(err?.response?.data?.detail || "Failed to load analytics.");
      }
    };

    load();
  }, [period, startDate, endDate]);

  return (
    <div>
      <PageHeader
        title="Analytics"
        subtitle="Review production efficiency, yield, output, and downtime trends."
      />

      <div className="filter-bar">
        <div className="form-group">
          <label>Summary Period</label>
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>

        <div className="form-group">
          <label>Start Date</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        </div>

        <div className="form-group">
          <label>End Date</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      {summary && (
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-label">Total Inflow</span>
            <strong className="stat-value">{formatNumber(summary.total_inflow)} tons</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total Output</span>
            <strong className="stat-value">{formatNumber(summary.total_output)} tons</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Average Yield</span>
            <strong className="stat-value">{formatNumber(summary.average_yield)}%</strong>
          </div>
          <div className="stat-card">
            <span className="stat-label">Total Downtime</span>
            <strong className="stat-value">{formatNumber(summary.total_downtime)} min</strong>
          </div>
        </div>
      )}

      <div className="charts-grid">
        <YieldTrendChart data={yieldTrend} />
        <InflowOutputChart data={inflowOutput} />
        <DowntimeTrendChart data={downtimeTrend} />
      </div>

      <Card title="Operational Insight">
        <p>
          Use this page to monitor yield variability, production throughput, and downtime exposure
          across selected dates. These indicators help management identify loss patterns,
          supplier-related issues, and process inefficiencies.
        </p>
      </Card>
    </div>
  );
}