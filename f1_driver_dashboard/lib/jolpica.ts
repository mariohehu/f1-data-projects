import { RaceResult, QualiResult } from "@/types/f1";

const BASE_URL = "https://api.jolpi.ca/ergast/f1";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function fetchAll(url: string): Promise<any[]> {
  const results: any[] = [];
  let offset = 0;
  const limit = 100;

  while (true) {
    const separator = url.includes("?") ? "&" : "?";
    const res = await fetch(`${url}${separator}limit=${limit}&offset=${offset}`, {
      next: { revalidate: 86400 },
    });
    if (!res.ok) break;
    const json = await res.json();
    const table = json?.MRData;
    if (!table) break;

    const total = parseInt(table.total ?? "0");
    const races =
      table.RaceTable?.Races ??
      table.DriverTable?.Drivers ??
      table.StandingsTable?.StandingsLists ??
      [];
    results.push(...races);

    offset += limit;
    if (offset >= total) break;

    await delay(260);
  }
  return results;
}

export async function fetchRaceResults(
  season: number,
  driverId: string
): Promise<RaceResult[]> {
  const url = `${BASE_URL}/${season}/drivers/${driverId}/results.json`;
  const races = await fetchAll(url);
  return races.map((race: any) => {
    const r = race.Results?.[0] ?? {};
    return {
      raceName: race.raceName,
      round: race.round,
      position: r.position ?? "NC",
      points: r.points ?? "0",
      grid: r.grid ?? "0",
      status: r.status ?? "Unknown",
      fastestLapRank: r.FastestLap?.rank,
    };
  });
}

export async function fetchQualiResults(
  season: number,
  driverId: string
): Promise<QualiResult[]> {
  const url = `${BASE_URL}/${season}/drivers/${driverId}/qualifying.json`;
  const races = await fetchAll(url);
  return races.map((race: any) => {
    const q = race.QualifyingResults?.[0] ?? {};
    return {
      raceName: race.raceName,
      round: race.round,
      position: q.position ?? "0",
      q1: q.Q1,
      q2: q.Q2,
      q3: q.Q3,
    };
  });
}

export async function fetchDriversForSeason(season: number): Promise<{ driverId: string; displayName: string }[]> {
  const url = `${BASE_URL}/${season}/drivers.json`;
  const drivers = await fetchAll(url);
  return drivers.map((d: any) => ({
    driverId: d.driverId,
    displayName: `${d.givenName} ${d.familyName}`,
  }));
}

export async function fetchDriverTeam(season: number, driverId: string): Promise<string> {
  try {
    const url = `${BASE_URL}/${season}/drivers/${driverId}/constructors.json`;
    const res = await fetch(`${url}?limit=1`, { next: { revalidate: 86400 } });
    const json = await res.json();
    return json?.MRData?.ConstructorTable?.Constructors?.[0]?.constructorId ?? "unknown";
  } catch {
    return "unknown";
  }
}
