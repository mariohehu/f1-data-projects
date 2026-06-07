"use client";
import { TrackPoint, CarPosition, RacePhase } from "@/types/tracker";
import { CarDot } from "./CarDot";

const PHASE_OVERLAY: Record<RacePhase, string | null> = {
  normal: null,
  safety_car: "rgba(255, 140, 0, 0.12)",
  vsc: "rgba(255, 200, 0, 0.12)",
  red_flag: "rgba(220, 0, 0, 0.15)",
};

const PHASE_LABEL: Record<RacePhase, string | null> = {
  normal: null,
  safety_car: "🟠 Safety Car",
  vsc: "🟡 Virtual Safety Car",
  red_flag: "🔴 Red Flag",
};

interface Props {
  trackPath: TrackPoint[];
  cars: CarPosition[];
  phase: RacePhase;
}

export function TrackSVG({ trackPath, cars, phase }: Props) {
  if (trackPath.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center text-gray-500">
        Loading track…
      </div>
    );
  }

  const pathData =
    trackPath.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";

  // sort cars by position (lower position number on top)
  const sortedCars = [...cars].sort((a, b) => (a.driver ?? 99) - (b.driver ?? 99));

  const overlay = PHASE_OVERLAY[phase];
  const label = PHASE_LABEL[phase];

  return (
    <div className="relative w-full h-full">
      <svg viewBox="0 0 1000 600" className="w-full h-full">
        {/* Phase background overlay */}
        {overlay && <rect x={0} y={0} width={1000} height={600} fill={overlay} />}

        {/* Track: thick grey outline then thinner road surface */}
        <path d={pathData} fill="none" stroke="#2a2a2a" strokeWidth={18} />
        <path d={pathData} fill="none" stroke="#444" strokeWidth={12} />
        <path d={pathData} fill="none" stroke="#666" strokeWidth={7} />

        {/* Cars */}
        {sortedCars.map((car, i) => (
          <CarDot key={car.driver} car={car} rank={i + 1} />
        ))}
      </svg>

      {/* Phase label overlay */}
      {label && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-black/70 text-white text-sm font-semibold px-4 py-1.5 rounded-full">
          {label}
        </div>
      )}
    </div>
  );
}
