export interface RaceResult {
  raceName: string;
  round: string;
  position: string;
  points: string;
  grid: string;
  status: string;
  fastestLapRank?: string;
}

export interface QualiResult {
  raceName: string;
  round: string;
  position: string;
  q1?: string;
  q2?: string;
  q3?: string;
}

export interface DriverStats {
  driverId: string;
  displayName: string;
  teamId: string;
  avgFinishPosition: number;
  pointsPerRace: number;
  dnfRate: number;
  podiumRate: number;
  winRate: number;
  avgQualiPosition: number;
  qualiToRaceDelta: number;
  polePositions: number;
  fastestLaps: number;
  racesEntered: number;
  seasonPoints: number;
  raceResults: RaceResult[];
}

export interface RadarDataPoint {
  metric: string;
  [driverId: string]: number | string;
}
