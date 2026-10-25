import { memo } from "react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import ChartCard, { anomalyDot, axisProps, ChartTooltip, shortDate } from "./ChartCard";

const formatPercent = (v) => `${Number(v).toFixed(2)}%`;
const YieldDot = anomalyDot("yield_anomaly", "var(--brand-600)");

function YieldTrendChart({ data = [], target }) {
  const anomalies = data.filter((d) => d.yield_anomaly).length;
  return (
    <ChartCard
      title="Yield Trend"
      meta={anomalies ? `${anomalies} unusual day${anomalies > 1 ? "s" : ""}` : `${data.length} days`}
      empty={!data.length}
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 12, right: 24, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--neutral-100)" vertical={false} />
          <XAxis dataKey="production_date" tickFormatter={shortDate} minTickGap={16} {...axisProps} />
          <YAxis unit="%" width={42} domain={[0, (max) => Math.max(40, Math.ceil(max / 5) * 5)]} {...axisProps} />
          <Tooltip content={<ChartTooltip format={formatPercent} />} />
          {target != null && (
            <ReferenceLine
              y={target}
              stroke="var(--kpi-green)"
              strokeDasharray="4 4"
              label={{ value: `Target ${target}%`, fontSize: 10, fill: "var(--kpi-green)", position: "insideTopRight" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="yield_percent"
            name="Yield"
            stroke="var(--brand-600)"
            strokeWidth={2.5}
            dot={<YieldDot />}
            activeDot={{ r: 6 }}
            isAnimationActive={data.length < 120}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export default memo(YieldTrendChart);
