import { NextRequest, NextResponse } from "next/server";
import { fetchRaceResults, fetchQualiResults, fetchDriverTeam } from "@/lib/jolpica";
import { computeStats } from "@/lib/stats";

export const revalidate = 86400;

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const driverId = searchParams.get("driverId");
  const displayName = searchParams.get("displayName") ?? driverId ?? "";
  const seasonFrom = parseInt(searchParams.get("from") ?? "2023");
  const seasonTo = parseInt(searchParams.get("to") ?? "2023");

  if (!driverId) {
    return NextResponse.json({ error: "driverId required" }, { status: 400 });
  }

  const allStats = [];

  for (let season = seasonFrom; season <= seasonTo; season++) {
    const [raceResults, qualiResults, teamId] = await Promise.all([
      fetchRaceResults(season, driverId),
      fetchQualiResults(season, driverId),
      fetchDriverTeam(season, driverId),
    ]);

    if (raceResults.length === 0) continue;

    const stats = computeStats(driverId, displayName, teamId, raceResults, qualiResults);
    allStats.push({ season, ...stats });
  }

  return NextResponse.json(allStats);
}
