import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import Card from "../common/Card";

export default function DowntimeTrendChart({ data = [] }) {
  return (
    <Card title="Downtime Trend">
      <div className="chart-box">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="production_date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="downtime_minutes" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}