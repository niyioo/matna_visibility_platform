import {
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";
import Card from "../common/Card";

export default function InflowOutputChart({ data = [] }) {
  return (
    <Card title="Inflow vs Output">
      <div className="chart-box">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="production_date" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="cassava_inflow_tons" name="Cassava Inflow" />
            <Bar dataKey="starch_output_tons" name="Starch Output" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}