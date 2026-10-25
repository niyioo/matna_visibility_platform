import { useState } from "react";
import { analyticsApi } from "../../api/analyticsApi";
import PageHeader from "../../components/common/PageHeader";
import { getErrorMessage, parseBlobError } from "../../utils/errors";
import usePlatformConfig from "../../hooks/usePlatformConfig";

const CUSTOM_PERIOD = { value: "custom", label: "Custom range", description: "Choose start and end dates" };

const FORMATS = [
  { type: "csv", label: "CSV spreadsheet", desc: "Opens in Excel. Includes a totals row.", btn: "btn-primary" },
  { type: "pdf", label: "PDF report", desc: "Formatted summary and daily table for management review.", btn: "btn-secondary" },
];

const DownloadIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

function filenameFrom(response, fallback) {
  const header = response.headers?.["content-disposition"] ?? "";
  const match = /filename="?([^";]+)"?/i.exec(header);
  return match?.[1] ?? fallback;
}

export default function ReportsPage() {
  const { periods, limits, today } = usePlatformConfig();
  const [period, setPeriod] = useState("weekly");
  const [range, setRange] = useState({ start: "", end: "" });
  const options = [...periods, CUSTOM_PERIOD];
  const [busy, setBusy] = useState(null);
  const [message, setMessage] = useState({ type: "", text: "" });

  const custom = period === "custom";
  const rangeEnd = range.end || today;
  const rangeInvalid = custom && (!range.start || range.start > rangeEnd);

  const download = async (type) => {
    setBusy(type);
    setMessage({ type: "", text: "" });
    try {
      const params = custom ? { start_date: range.start, end_date: rangeEnd } : { period };
      const response = await analyticsApi.downloadReport(type, params);
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = filenameFrom(response, `matna_production_report.${type}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setMessage({ type: "success", text: `${type.toUpperCase()} report downloaded.` });
    } catch (error) {
      await parseBlobError(error);
      setMessage({ type: "error", text: getErrorMessage(error, "Download failed. Please try again.") });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      <PageHeader title="Reports" subtitle="Export production data for management review or record keeping. Voided entries are excluded." />

      <section className="card" aria-labelledby="report-period-title" style={{ marginBottom: "var(--space-5)" }}>
        <div className="card-header"><h3 id="report-period-title">Report period</h3></div>
        <div className="card-body">
          <div className="segmented" role="radiogroup" aria-labelledby="report-period-title">
            {options.map((p) => (
              <button
                key={p.value}
                type="button"
                role="radio"
                aria-checked={period === p.value}
                className={`segmented-option${period === p.value ? " active" : ""}`}
                onClick={() => setPeriod(p.value)}
              >
                <span>{p.label}</span>
                <small>{p.description}</small>
              </button>
            ))}
          </div>

          {custom && (
            <div className="filter-inline">
              <div className="form-group">
                <label htmlFor="rep-start">From</label>
                <input id="rep-start" type="date" value={range.start} max={rangeEnd}
                  onChange={(e) => setRange((r) => ({ ...r, start: e.target.value }))} />
              </div>
              <div className="form-group">
                <label htmlFor="rep-end">To</label>
                <input id="rep-end" type="date" value={rangeEnd} min={range.start || undefined} max={today}
                  onChange={(e) => setRange((r) => ({ ...r, end: e.target.value }))} />
              </div>
              {limits && <span className="muted-small">Maximum range: {limits.max_range_days} days.</span>}
            </div>
          )}
        </div>
      </section>

      {message.text && (
        <div className={`alert ${message.type}`} role={message.type === "error" ? "alert" : "status"} style={{ marginBottom: "var(--space-4)" }}>
          {message.text}
        </div>
      )}

      <div className="page-grid">
        {FORMATS.map(({ type, label, desc, btn }) => (
          <section className="card" key={type} aria-label={label}>
            <div className="card-body report-card">
              <div>
                <h3>{label}</h3>
                <p className="muted-small">{desc}</p>
              </div>
              <button className={`btn ${btn}`} onClick={() => download(type)} disabled={busy !== null || rangeInvalid}>
                {busy === type ? "Preparing…" : <><DownloadIcon /> Download {type.toUpperCase()}</>}
              </button>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
