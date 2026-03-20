import { useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import Card from "../../components/common/Card";
import api from "../../api/axios";

export default function ReportsPage() {
  const [period, setPeriod] = useState("daily");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const downloadReport = async (type) => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get(`/analytics/reports/export/${type}/?period=${period}`, {
        responseType: "blob"
      });

      const blob = new Blob([response.data], {
        type: type === "pdf" ? "application/pdf" : "text/csv"
      });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `production_${period}_report.${type}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      setError("Failed to download report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Reports"
        subtitle="Export production summaries in CSV or PDF format."
      />

      <Card title="Export Reports">
        <div className="filter-bar">
          <div className="form-group">
            <label>Period</label>
            <select value={period} onChange={(e) => setPeriod(e.target.value)}>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <div className="actions-row">
            <button
              className="btn btn-primary"
              onClick={() => downloadReport("csv")}
              disabled={loading}
            >
              Download CSV
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => downloadReport("pdf")}
              disabled={loading}
            >
              Download PDF
            </button>
          </div>
        </div>

        {error && <div className="alert error">{error}</div>}
      </Card>
    </div>
  );
}