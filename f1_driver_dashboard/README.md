# F1 Driver Performance Dashboard

A Next.js web app that compares **any two F1 drivers across seasons** with radar charts, bar charts, and trend lines. Built on the Jolpica API (the drop-in successor to Ergast).

![Next.js](https://img.shields.io/badge/Next.js-14-black) ![TypeScript](https://img.shields.io/badge/TypeScript-5-blue) ![Recharts](https://img.shields.io/badge/charts-Recharts-purple)

---

## What it does

Pick two drivers and a season range, and get a head-to-head breakdown: average finish, points per race, podium/win rates, DNF rate, qualifying pace, and season-over-season trends.

## Quickstart

```bash
npm install
npm run dev
# open http://localhost:3000
```

## Metrics

| Metric | Definition |
|--------|------------|
| Avg Finish Position | mean finishing position (lower = better) |
| Points / Race | total points ÷ races entered |
| Podium Rate | podiums ÷ **races finished** |
| Win Rate | wins ÷ **races finished** |
| DNF Rate | DNFs ÷ races entered |
| Avg Quali Position | mean grid position |
| Quali→Race Delta | how many places gained/lost vs. grid |

> Podium and win rates are computed over *finishes*, not entries, so a reliability problem doesn't unfairly depress a driver's strike rate.

## Architecture

```
app/
├── page.tsx                    # landing — driver selectors + season range
├── compare/page.tsx            # comparison dashboard
└── api/
    ├── driver-stats/route.ts   # fetches + computes per-driver stats
    └── drivers/route.ts        # season driver list
components/                     # RadarComparison, StatsBarChart, SeasonTrendLine, StatCard, DriverSelector
lib/
├── jolpica.ts                  # API client (paginated, rate-limited)
└── stats.ts                    # metric calculations + radar normalisation
```

## Key design decisions

- **Server-side API calls** (Next.js route handlers) avoid CORS and enable 24h caching via `revalidate`.
- **Rate limiting** — Jolpica allows ~4 req/sec; the client paginates with a 260ms delay between pages to stay under the limit.
- **Multi-season aggregation** — counting stats (poles, fastest laps) are *summed* across seasons; rate stats are *averaged*. Team colour uses the team the driver spent the most seasons at.
- **Radar normalisation** — all six metrics scaled 0-100 with direction-aware inversion (lower-is-better metrics flipped).

## Charts

- **Radar** — 6 normalised metrics, both drivers overlaid
- **Bar grid** — one chart per metric, side by side
- **Season trend** — points-per-race line over the selected range
- **Stat cards** — head-to-head with the better value starred

## Data source

[Jolpica API](https://github.com/jolpica/jolpica-f1) — `https://api.jolpi.ca/ergast/f1/`. Drop-in replacement for the Ergast API, which shut down in late 2024.
