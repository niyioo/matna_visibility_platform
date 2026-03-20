import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatCard from "../../components/common/StatCard";
import Loader from "../../components/common/Loader";
import YieldTrendChart from "../../components/dashboard/YieldTrendChart";
import InflowOutputChart from "../../components/dashboard/InflowOutputChart";
import DowntimeTrendChart from "../../components/dashboard/DowntimeTrendChart";
import { analyticsApi } from "../../api/analyticsApi";
import { formatDate, formatNumber } from "../../utils/formatters";

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState(null);
  const [yieldTrend, setYieldTrend] = useState([]);
  const [inflowOutput, setInflowOutput] = useState([]);
  const [downtimeTrend, setDowntimeTrend] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setError("");

        const [dashboardData, yieldData, inflowData, downtimeData] =
          await Promise.all([
            analyticsApi.getDashboard(),
            analyticsApi.getYieldTrend(),
            analyticsApi.getInflowVsOutput(),
            analyticsApi.getDowntimeTrend()
          ]);

        setDashboard(dashboardData);
        setYieldTrend(yieldData);
        setInflowOutput(inflowData);
        setDowntimeTrend(downtimeData);
      } catch (err) {
        console.error("Dashboard load error:", err);
        setError(
          err?.response?.data?.detail || "Failed to load dashboard data."
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) return <Loader />;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={
          dashboard?.snapshot_date
            ? `Latest operational snapshot as of ${formatDate(dashboard.snapshot_date)}.`
            : "No production snapshot available yet."
        }
      />

      {error && <div className="alert error">{error}</div>}

      <div className="stats-grid">
        <StatCard label="Latest Inflow" value={formatNumber(dashboard?.latest_inflow)} suffix=" tons" />
        <StatCard label="Latest Output" value={formatNumber(dashboard?.latest_output)} suffix=" tons" />
        <StatCard label="Latest Yield" value={formatNumber(dashboard?.latest_yield)} suffix="%" />
        <StatCard label="Latest Downtime" value={formatNumber(dashboard?.latest_downtime)} suffix=" min" />
        <StatCard label="Raw Cassava Stock" value={formatNumber(dashboard?.raw_cassava_stock)} suffix=" tons" />
        <StatCard label="Finished Starch Stock" value={formatNumber(dashboard?.finished_starch_stock)} suffix=" tons" />
      </div>

      <div className="charts-grid">
        <YieldTrendChart data={yieldTrend} />
        <InflowOutputChart data={inflowOutput} />
        <DowntimeTrendChart data={downtimeTrend} />
      </div>
    </div>
  );
}