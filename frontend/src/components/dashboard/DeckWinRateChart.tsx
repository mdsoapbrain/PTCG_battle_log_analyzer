import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { DeckStat } from "@/types/api";

interface DeckWinRateChartProps {
  data: DeckStat[];
}

export function DeckWinRateChart({ data }: DeckWinRateChartProps) {
  const chartData = data.map((d) => ({
    name: d.deck_name.length > 18 ? d.deck_name.slice(0, 16) + "…" : d.deck_name,
    winRate: d.win_rate,
    total: d.matches,
  }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
        <XAxis type="number" domain={[0, 100]} tick={{ fill: "hsl(215 12% 50%)", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" width={130} tick={{ fill: "hsl(210 20% 82%)", fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: "hsl(220 18% 12%)", border: "1px solid hsl(220 14% 18%)", borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: "hsl(210 20% 92%)" }}
          formatter={(value: number) => [`${value.toFixed(1)}%`, "Win Rate"]}
        />
        <Bar dataKey="winRate" radius={[0, 4, 4, 0]} maxBarSize={28}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.winRate >= 55 ? "hsl(152 60% 48%)" : entry.winRate >= 45 ? "hsl(45 93% 58%)" : "hsl(0 72% 51%)"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
