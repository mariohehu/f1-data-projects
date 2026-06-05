"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";

interface SeasonPoint {
  season: number;
  pointsPerRace: number;
}

interface Props {
  seriesA: SeasonPoint[];
  seriesB: SeasonPoint[];
  nameA: string;
  nameB: string;
  colorA: string;
  colorB: string;
}

export function SeasonTrendLine({ seriesA, seriesB, nameA, nameB, colorA, colorB }: Props) {
  const seasons = Array.from(
    new Set([...seriesA.map((d) => d.season), ...seriesB.map((d) => d.season)])
  ).sort();

  const data = seasons.map((s) => ({
    season: s,
    [nameA]: seriesA.find((d) => d.season === s)?.pointsPerRace ?? null,
    [nameB]: seriesB.find((d) => d.season === s)?.pointsPerRace ?? null,
  }));

  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h3 className="text-white font-semibold mb-3">Points per Race — Season Trend</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="season" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
          <YAxis tick={{ fill: "#9CA3AF", fontSize: 12 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1F2937", border: "none", borderRadius: 8 }}
            labelStyle={{ color: "#fff" }}
            formatter={(v: number) => [v?.toFixed(1) ?? "N/A", ""]}
          />
          <Legend />
          <Line type="monotone" dataKey={nameA} stroke={colorA} strokeWidth={2} dot={{ r: 4 }} connectNulls />
          <Line type="monotone" dataKey={nameB} stroke={colorB} strokeWidth={2} dot={{ r: 4 }} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
