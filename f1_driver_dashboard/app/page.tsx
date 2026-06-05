"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { DriverSelector } from "@/components/DriverSelector";

interface Driver {
  driverId: string;
  displayName: string;
}

const SEASONS = Array.from({ length: 15 }, (_, i) => 2024 - i);

export default function HomePage() {
  const router = useRouter();
  const [season, setSeason] = useState(2023);
  const [driverA, setDriverA] = useState<Driver | null>(null);
  const [driverB, setDriverB] = useState<Driver | null>(null);
  const [fromSeason, setFromSeason] = useState(2020);
  const [toSeason, setToSeason] = useState(2023);

  const canCompare = driverA && driverB && driverA.driverId !== driverB.driverId;

  function handleCompare() {
    if (!canCompare) return;
    const params = new URLSearchParams({
      d1: driverA.driverId,
      d2: driverB.driverId,
      n1: driverA.displayName,
      n2: driverB.displayName,
      from: String(fromSeason),
      to: String(toSeason),
    });
    router.push(`/compare?${params.toString()}`);
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl w-full">
        <h1 className="text-4xl font-bold text-center mb-2">
          🏎 F1 Driver Dashboard
        </h1>
        <p className="text-gray-400 text-center mb-10">
          Compare any two drivers across seasons
        </p>

        <div className="bg-gray-900 rounded-2xl p-8 flex flex-col gap-6">
          {/* Season for driver list */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold text-gray-300">Driver list season</label>
            <select
              value={season}
              onChange={(e) => setSeason(Number(e.target.value))}
              className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none"
            >
              {SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          {/* Driver selectors */}
          <div className="grid grid-cols-2 gap-4">
            <DriverSelector season={season} label="Driver A" value={driverA} onChange={setDriverA} />
            <DriverSelector season={season} label="Driver B" value={driverB} onChange={setDriverB} />
          </div>

          {/* Season range */}
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm font-semibold text-gray-300">From Season</label>
              <select
                value={fromSeason}
                onChange={(e) => setFromSeason(Number(e.target.value))}
                className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none"
              >
                {SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm font-semibold text-gray-300">To Season</label>
              <select
                value={toSeason}
                onChange={(e) => setToSeason(Number(e.target.value))}
                className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none"
              >
                {SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <button
            onClick={handleCompare}
            disabled={!canCompare}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-xl font-semibold text-lg transition-colors"
          >
            Compare Drivers →
          </button>
        </div>
      </div>
    </main>
  );
}
