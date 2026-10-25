import { memo } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import ChartCard, { axisProps, ChartTooltip, shortDate } from "./ChartCard";

const formatTons = (v) => `${Number(v).toLocaleString("en-NG", { maximumFractionDigits: 2 })} t`;

function InflowOutputChart({ data = [] }) {
  return (
    <ChartCard title="Cassava Inflow vs Starch Output" meta="tons" empty={!data.length}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 12, right: 24, left: 0, bottom: 0 }} barCategoryGap="30%">
          <CartesianGrid strokeDasharray="3 3" stroke="var(--neutral-100)" vertical={false} />
          <XAxis dataKey="production_date" tickFormatter={shortDate} minTickGap={16} {...axisProps} />
          <YAxis width={48} {...axisProps} />
          <Tooltip content={<ChartTooltip format={formatTons} />} cursor={{ fill: "var(--neutral-50)" }} />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
          <Bar dataKey="cassava_inflow_tons" name="Cassava inflow" fill="var(--brand-600)" radius={[3, 3, 0, 0]} isAnimationActive={data.length < 120} />
          <Bar dataKey="starch_output_tons" name="Starch output" fill="var(--kpi-teal)" radius={[3, 3, 0, 0]} isAnimationActive={data.length < 120} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export default memo(InflowOutputChart);
