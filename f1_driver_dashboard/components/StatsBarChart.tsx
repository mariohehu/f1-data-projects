"use client";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";

interface Props {
  data: Array<{ label: string; driverA: number; driverB: number }>;
  nameA: string;
  nameB: string;
  colorA: string;
  colorB: string;
  title: string;
  formatter?: (v: number) => string;
}

export function StatsBarChart({ data, nameA, nameB, colorA, colorB, title, formatter }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl p-4">
      <h3 className="text-white font-semibold mb-3 text-sm">{title}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="label" tick={{ fill: "#9CA3AF", fontSize: 11 }} />
          <YAxis tick={{ fill: "#9CA3AF", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1F2937", border: "none", borderRadius: 8 }}
            labelStyle={{ color: "#fff" }}
            formatter={(v: number) => [formatter ? formatter(v) : v.toFixed(2)]}
          />
          <Legend />
          <Bar dataKey="driverA" name={nameA} fill={colorA} radius={[4, 4, 0, 0]} />
          <Bar dataKey="driverB" name={nameB} fill={colorB} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
