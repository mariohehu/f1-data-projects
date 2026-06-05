"use client";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Legend, ResponsiveContainer, Tooltip,
} from "recharts";

interface Props {
  data: Array<{ metric: string; [key: string]: number | string }>;
  driverA: { id: string; name: string; color: string };
  driverB: { id: string; name: string; color: string };
}

export function RadarComparison({ data, driverA, driverB }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h3 className="text-white font-semibold mb-3">Performance Radar</h3>
      <ResponsiveContainer width="100%" height={320}>
        <RadarChart data={data}>
          <PolarGrid stroke="#374151" />
          <PolarAngleAxis dataKey="metric" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          <Radar
            name={driverA.name}
            dataKey={driverA.id}
            stroke={driverA.color}
            fill={driverA.color}
            fillOpacity={0.25}
          />
          <Radar
            name={driverB.name}
            dataKey={driverB.id}
            stroke={driverB.color}
            fill={driverB.color}
            fillOpacity={0.25}
          />
          <Legend />
          <Tooltip
            contentStyle={{ backgroundColor: "#1F2937", border: "none", borderRadius: 8 }}
            labelStyle={{ color: "#fff" }}
            formatter={(val: number) => [`${val.toFixed(1)} / 100`]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
