"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { CarPosition } from "@/types/tracker";

export function useReplay(
  allPositions: CarPosition[],
  driverMap: Record<number, { acronym: string; team_colour: string }>
) {
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // initialise time to first position timestamp
  useEffect(() => {
    if (allPositions.length === 0) return;
    const first = Math.min(...allPositions.map((p) => new Date(p.date).getTime()));
    setCurrentTime(first);
  }, [allPositions]);

  // playback ticker
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (!playing) return;

    intervalRef.current = setInterval(() => {
      setCurrentTime((t) => {
        const max = Math.max(...allPositions.map((p) => new Date(p.date).getTime()));
        if (t >= max) { setPlaying(false); return t; }
        return t + 500 * speed;
      });
    }, 500);

    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, speed, allPositions]);

  // current positions = latest per driver up to currentTime
  const currentPositions: CarPosition[] = (() => {
    const seen = new Map<number, CarPosition>();
    for (const pos of allPositions) {
      const t = new Date(pos.date).getTime();
      if (t > currentTime) continue;
      const existing = seen.get(pos.driver);
      if (!existing || new Date(pos.date) > new Date(existing.date)) {
        seen.set(pos.driver, pos);
      }
    }
    return Array.from(seen.values()).map((pos) => ({
      ...pos,
      acronym: driverMap[pos.driver]?.acronym ?? "???",
      color: driverMap[pos.driver]?.team_colour ?? "#AAAAAA",
    }));
  })();

  const minTime = allPositions.length
    ? Math.min(...allPositions.map((p) => new Date(p.date).getTime()))
    : 0;
  const maxTime = allPositions.length
    ? Math.max(...allPositions.map((p) => new Date(p.date).getTime()))
    : 0;

  const progress = maxTime > minTime ? (currentTime - minTime) / (maxTime - minTime) : 0;

  return {
    currentPositions,
    playing,
    setPlaying,
    speed,
    setSpeed,
    progress,
    currentTime,
    setCurrentTime,
    minTime,
    maxTime,
  };
}
