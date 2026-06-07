export interface TrackPoint { x: number; y: number; }

export interface CarPosition {
  driver: number;
  x: number;
  y: number;
  acronym: string;
  color: string;
  date: string;
}

export interface DriverInfo {
  acronym: string;
  team_colour: string;
  full_name?: string;
}

export type RacePhase = "normal" | "safety_car" | "vsc" | "red_flag";

export interface WebSocketMessage {
  type: "init" | "positions" | "error";
  track?: TrackPoint[];
  drivers?: Record<number, DriverInfo>;
  data?: CarPosition[];
  phase?: RacePhase;
  timestamp?: string;
  message?: string;
}

export interface Session {
  session_key: number;
  session_name: string;
  year: number;
  country_name: string;
  circuit_short_name: string;
  date_start: string;
}
