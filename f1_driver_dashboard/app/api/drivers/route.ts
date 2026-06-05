import { NextRequest, NextResponse } from "next/server";
import { fetchDriversForSeason } from "@/lib/jolpica";

export const revalidate = 86400;

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const season = parseInt(searchParams.get("season") ?? "2023");
  const drivers = await fetchDriversForSeason(season);
  return NextResponse.json(drivers);
}
