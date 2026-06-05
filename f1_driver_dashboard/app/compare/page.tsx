"use client";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { DriverStats } from "@/types/f1";
import { buildRadarData } from "@/lib/stats";
import { RadarComparison } from "@/components/RadarComparison";
import { StatsBarChart } from "@/components/StatsBarChart";
import { SeasonTrendLine } from "@/components/SeasonTrendLine";
import { StatCard } from "@/components/StatCard";

const TEAM_COLORS: Record<string, string> = {
  red_bull: "#3671C6",
  mercedes: "#27F4D2",
  ferrari: "#E8002D",
  mclaren: "#FF8000",
  aston_martin: "#229971",
  alpine: "#FF87BC",
  williams: "#64C4FF",
  alphatauri: "#5E8FAA",
  alfa: "#C92D4B",
  haas: "#B6BABD",
  unknown: "#AAAAAA",
};

function getColor(teamId?: string) {
  return TEAM_COLORS[teamId ?? "unknown"] ?? "#AAAAAA";
}

function pct(v: number) { return `${(v * 100).toFixed(1)}%`; }
function pts(v: number) { return v.toFixed(1); }
function pos(v: number) { return `P${v.toFixed(1)}`; }

function ComparePage() {
  const params = useSearchParams();
  const d1 = params.get("d1") ?? "";
  const d2 = params.get("d2") ?? "";
  const n1 = params.get("n1") ?? d1;
  const n2 = params.get("n2") ?? d2;
  const from = params.get("from") ?? "2023";
  const to = params.get("to") ?? "2023";

  const [statsA, setStatsA] = useState<(DriverStats & { season: number })[]>([]);
  const [statsB, setStatsB] = useState<(DriverStats & { season: number })[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!d1 || !d2) return;
    setLoading(true);
    Promise.all([
      fetch(`/api/driver-stats?driverId=${d1}&displayName=${encodeURIComponent(n1)}&from=${from}&to=${to}`).then(r => r.json()),
      fetch(`/api/driver-stats?driverId=${d2}&displayName=${encodeURIComponent(n2)}&from=${from}&to=${to}`).then(r => r.json()),
    ])
      .then(([a, b]) => { setStatsA(a); setStatsB(b); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [d1, d2, n1, n2, from, to]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <p className="text-xl animate-pulse">Loading stats from Jolpica API...</p>
      </div>
    );
  }

  if (error || !statsA.length || !statsB.length) {
    return (
      <div className="min-h-screen bg-gray-950 text-white flex items-center justify-center">
        <p className="text-red-400">{error ?? "No data found for selected range."}</p>
      </div>
    );
  }

  // aggregate across seasons
  const aggStat = (arr: (DriverStats & { season: number })[]): DriverStats => {
    const total = arr.length;
    const avg = <K extends keyof DriverStats>(key: K) =>
      arr.reduce((s, x) => s + (x[key] as number), 0) / total;
    const sum = <K extends keyof DriverStats>(key: K) =>
      arr.reduce((s, x) => s + (x[key] as number), 0);

    const averagedKeys = ["avgFinishPosition","pointsPerRace","dnfRate","podiumRate","winRate",
        "avgQualiPosition","qualiToRaceDelta"] as const;
    const summedKeys = ["polePositions","fastestLaps"] as const;

    // use the team they spent the most seasons at for color
    const teamCounts = arr.reduce((acc, x) => {
      acc[x.teamId] = (acc[x.teamId] ?? 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const primaryTeam = Object.entries(teamCounts).sort((a, b) => b[1] - a[1])[0]?.[0]
      ?? arr[arr.length - 1].teamId;

    return { ...arr[arr.length - 1],
      ...Object.fromEntries(averagedKeys.map(k => [k, avg(k)])),
      ...Object.fromEntries(summedKeys.map(k => [k, sum(k)])),
      teamId: primaryTeam,
    } as DriverStats;
  };

  const aggA = aggStat(statsA);
  const aggB = aggStat(statsB);
  const colorA = getColor(aggA.teamId);
  const colorB = getColor(aggB.teamId);
  const radarData = buildRadarData(aggA, aggB);

  const barMetrics = [
    { label: "Avg Finish", vA: aggA.avgFinishPosition, vB: aggB.avgFinishPosition, fmt: pos },
    { label: "Points/Race", vA: aggA.pointsPerRace, vB: aggB.pointsPerRace, fmt: pts },
    { label: "Podium %", vA: aggA.podiumRate * 100, vB: aggB.podiumRate * 100, fmt: (v: number) => `${v.toFixed(1)}%` },
    { label: "Win %", vA: aggA.winRate * 100, vB: aggB.winRate * 100, fmt: (v: number) => `${v.toFixed(1)}%` },
    { label: "DNF %", vA: aggA.dnfRate * 100, vB: aggB.dnfRate * 100, fmt: (v: number) => `${v.toFixed(1)}%` },
    { label: "Avg Quali", vA: aggA.avgQualiPosition, vB: aggB.avgQualiPosition, fmt: pos },
  ];

  return (
    <main className="min-h-screen bg-gray-950 text-white p-6">
      <div className="max-w-6xl mx-auto flex flex-col gap-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <a href="/" className="text-gray-400 hover:text-white text-sm">← Back</a>
          <h1 className="text-2xl font-bold">
            <span style={{ color: colorA }}>{n1}</span>
            <span className="text-gray-400 mx-3">vs</span>
            <span style={{ color: colorB }}>{n2}</span>
          </h1>
          <span className="text-gray-400 text-sm">{from}–{to}</span>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {barMetrics.map((m) => (
            <StatCard
              key={m.label}
              label={m.label}
              valueA={m.fmt(m.vA)}
              valueB={m.fmt(m.vB)}
              colorA={colorA}
              colorB={colorB}
              better={
                m.label === "Avg Finish" || m.label === "Avg Quali" || m.label === "DNF %"
                  ? m.vA < m.vB ? "A" : "B"
                  : m.vA > m.vB ? "A" : "B"
              }
            />
          ))}
        </div>

        {/* Radar */}
        <RadarComparison
          data={radarData}
          driverA={{ id: d1, name: n1, color: colorA }}
          driverB={{ id: d2, name: n2, color: colorB }}
        />

        {/* Bar charts grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {barMetrics.map((m) => (
            <StatsBarChart
              key={m.label}
              title={m.label}
              data={[{ label: m.label, driverA: m.vA, driverB: m.vB }]}
              nameA={n1} nameB={n2}
              colorA={colorA} colorB={colorB}
              formatter={m.fmt}
            />
          ))}
        </div>

        {/* Season trend */}
        <SeasonTrendLine
          seriesA={statsA.map(s => ({ season: s.season, pointsPerRace: s.pointsPerRace }))}
          seriesB={statsB.map(s => ({ season: s.season, pointsPerRace: s.pointsPerRace }))}
          nameA={n1} nameB={n2}
          colorA={colorA} colorB={colorB}
        />
      </div>
    </main>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gray-950 text-white flex items-center justify-center"><p>Loading...</p></div>}>
      <ComparePage />
    </Suspense>
  );
}
