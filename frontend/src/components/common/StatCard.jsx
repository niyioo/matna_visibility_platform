export default function StatCard({ label, value, suffix = "" }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <strong className="stat-value">
        {value}{suffix}
      </strong>
    </div>
  );
}