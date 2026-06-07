"use client";
import { CarPosition } from "@/types/tracker";

interface Props {
  cars: CarPosition[];
}

export function TimingTower({ cars }: Props) {
  return (
    <div className="flex flex-col gap-0.5 w-40 flex-shrink-0">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Positions</p>
      {cars.map((car, i) => (
        <div
          key={car.driver}
          className="flex items-center gap-2 px-2 py-1 rounded bg-gray-800/80"
        >
          <span className="text-xs text-gray-400 w-4 text-right">{i + 1}</span>
          <span
            className="w-2 h-2 rounded-full flex-shrink-0"
            style={{ backgroundColor: car.color }}
          />
          <span className="text-xs font-mono font-bold text-white">{car.acronym}</span>
        </div>
      ))}
    </div>
  );
}
