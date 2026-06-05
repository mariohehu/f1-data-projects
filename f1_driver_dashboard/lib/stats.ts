import { RaceResult, QualiResult, DriverStats } from "@/types/f1";

const FINISHED_STATUSES = ["Finished", "+1 Lap", "+2 Laps", "+3 Laps", "+4 Laps", "+5 Laps"];

function isDNF(status: string): boolean {
  return !FINISHED_STATUSES.some((s) => status.includes(s)) && !status.startsWith("+");
}

export function computeStats(
  driverId: string,
  displayName: string,
  teamId: string,
  raceResults: RaceResult[],
  qualiResults: QualiResult[]
): DriverStats {
  const entered = raceResults.length;
  if (entered === 0) {
    return {
      driverId,
      displayName,
      teamId,
      avgFinishPosition: 0,
      pointsPerRace: 0,
      dnfRate: 0,
      podiumRate: 0,
      winRate: 0,
      avgQualiPosition: 0,
      qualiToRaceDelta: 0,
      polePositions: 0,
      fastestLaps: 0,
      racesEntered: 0,
      seasonPoints: 0,
      raceResults,
    };
  }

  const finishPositions = raceResults
    .map((r) => parseInt(r.position))
    .filter((p) => !isNaN(p));

  const avgFinishPosition =
    finishPositions.reduce((a, b) => a + b, 0) / Math.max(finishPositions.length, 1);

  const totalPoints = raceResults.reduce((sum, r) => sum + parseFloat(r.points ?? "0"), 0);
  const pointsPerRace = totalPoints / entered;
  const dnfs = raceResults.filter((r) => isDNF(r.status)).length;
  const dnfRate = dnfs / entered;
  const finishes = Math.max(finishPositions.length, 1);
  const podiumRate = finishPositions.filter((p) => p <= 3).length / finishes;
  const winRate = finishPositions.filter((p) => p === 1).length / finishes;
  const polePositions = raceResults.filter((r) => r.grid === "1").length;
  const fastestLaps = raceResults.filter((r) => r.fastestLapRank === "1").length;

  const qualiPositions = qualiResults
    .map((q) => parseInt(q.position))
    .filter((p) => !isNaN(p) && p > 0);

  const avgQualiPosition =
    qualiPositions.length > 0
      ? qualiPositions.reduce((a, b) => a + b, 0) / qualiPositions.length
      : avgFinishPosition;

  const qualiToRaceDelta = avgFinishPosition - avgQualiPosition;

  return {
    driverId,
    displayName,
    teamId,
    avgFinishPosition,
    pointsPerRace,
    dnfRate,
    podiumRate,
    winRate,
    avgQualiPosition,
    qualiToRaceDelta,
    polePositions,
    fastestLaps,
    racesEntered: entered,
    seasonPoints: totalPoints,
    raceResults,
  };
}

export function normalizeMetric(
  value: number,
  min: number,
  max: number,
  higherIsBetter: boolean
): number {
  if (max === min) return 50;
  const normalized = ((value - min) / (max - min)) * 100;
  const clamped = Math.min(100, Math.max(0, normalized));
  return higherIsBetter ? clamped : 100 - clamped;
}

export function buildRadarData(statsA: DriverStats, statsB: DriverStats) {
  const metrics = [
    {
      key: "avgFinishPosition",
      label: "Avg Finish",
      higherIsBetter: false,
      min: 1,
      max: 20,
    },
    {
      key: "pointsPerRace",
      label: "Points/Race",
      higherIsBetter: true,
      min: 0,
      max: 25,
    },
    {
      key: "podiumRate",
      label: "Podium Rate",
      higherIsBetter: true,
      min: 0,
      max: 1,
    },
    {
      key: "winRate",
      label: "Win Rate",
      higherIsBetter: true,
      min: 0,
      max: 1,
    },
    {
      key: "dnfRate",
      label: "Reliability",
      higherIsBetter: false,
      min: 0,
      max: 0.3,
    },
    {
      key: "avgQualiPosition",
      label: "Quali Pace",
      higherIsBetter: false,
      min: 1,
      max: 20,
    },
  ] as const;

  return metrics.map((m) => ({
    metric: m.label,
    [statsA.driverId]: normalizeMetric(
      statsA[m.key] as number,
      m.min,
      m.max,
      m.higherIsBetter
    ),
    [statsB.driverId]: normalizeMetric(
      statsB[m.key] as number,
      m.min,
      m.max,
      m.higherIsBetter
    ),
  }));
}
