import { memo } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import ChartCard, { anomalyDot, axisProps, ChartTooltip, shortDate } from "./ChartCard";

const formatMinutes = (v) => `${Number(v).toLocaleString()} min`;
const DowntimeDot = anomalyDot("downtime_anomaly", "var(--kpi-amber)");

function DowntimeTrendChart({ data = [] }) {
  const total = data.reduce((sum, d) => sum + (Number(d.downtime_minutes) || 0), 0);
  return (
    <ChartCard title="Downtime Trend" meta={`${total.toLocaleString()} min total`} empty={!data.length}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 12, right: 24, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="downtimeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--kpi-amber)" stopOpacity={0.18} />
              <stop offset="95%" stopColor="var(--kpi-amber)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--neutral-100)" vertical={false} />
          <XAxis dataKey="production_date" tickFormatter={shortDate} minTickGap={16} {...axisProps} />
          <YAxis width={42} allowDecimals={false} {...axisProps} />
          <Tooltip content={<ChartTooltip format={formatMinutes} />} />
          <Area
            type="monotone"
            dataKey="downtime_minutes"
            name="Downtime"
            stroke="var(--kpi-amber)"
            strokeWidth={2.5}
            fill="url(#downtimeGrad)"
            dot={<DowntimeDot />}
            activeDot={{ r: 6 }}
            isAnimationActive={data.length < 120}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export default memo(DowntimeTrendChart);
