"use client";
import { useState, useCallback, useEffect } from "react";
import { TrackSVG } from "@/components/TrackSVG";
import { TimingTower } from "@/components/TimingTower";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useReplay } from "@/hooks/useReplay";
import { CarPosition, TrackPoint, RacePhase, Session } from "@/types/tracker";

const API = "http://localhost:8001";
const WS = "ws://localhost:8001";

// OpenF1 location data is only available from 2023 onward.
// Values are the exact OpenF1 circuit_short_name for reliable matching.
const REPLAY_SEASONS = [2024, 2023];
const REPLAY_RACES: Record<number, { label: string; circuit: string }[]> = {
  2024: [
    { label: "Monza", circuit: "Monza" },
    { label: "Monaco", circuit: "Monte Carlo" },
    { label: "Silverstone", circuit: "Silverstone" },
    { label: "Spa-Francorchamps", circuit: "Spa-Francorchamps" },
    { label: "Suzuka", circuit: "Suzuka" },
    { label: "Las Vegas", circuit: "Las Vegas" },
  ],
  2023: [
    { label: "Monza", circuit: "Monza" },
    { label: "Monaco", circuit: "Monte Carlo" },
    { label: "Silverstone", circuit: "Silverstone" },
    { label: "Spa-Francorchamps", circuit: "Spa-Francorchamps" },
    { label: "Suzuka", circuit: "Suzuka" },
    { label: "Interlagos (Brazil)", circuit: "Interlagos" },
  ],
};

export default function TrackerPage() {
  const [mode, setMode] = useState<"live" | "replay">("replay");

  // live state
  const [sessions, setSessions] = useState<Session[]>([]);
  const [liveSession, setLiveSession] = useState<Session | null>(null);
  const [liveTrack, setLiveTrack] = useState<TrackPoint[]>([]);
  const [liveCars, setLiveCars] = useState<CarPosition[]>([]);
  const [livePhase, setLivePhase] = useState<RacePhase>("normal");
  const [wsUrl, setWsUrl] = useState<string | null>(null);

  // replay state
  const [replaySeason, setReplaySeason] = useState(2023);
  const [replayRace, setReplayRace] = useState("Monza"); // holds circuit_short_name
  const [replayTrack, setReplayTrack] = useState<TrackPoint[]>([]);
  const [replayPositions, setReplayPositions] = useState<CarPosition[]>([]);
  const [replayDrivers, setReplayDrivers] = useState<Record<number, { acronym: string; team_colour: string }>>({});
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<string | null>(null);

  const replay = useReplay(replayPositions, replayDrivers);

  // Load live sessions
  useEffect(() => {
    fetch(`${API}/sessions?year=2024&session_name=Race`)
      .then((r) => r.json())
      .then(setSessions)
      .catch(() => {});
  }, []);

  // WebSocket handler
  const handleWsMessage = useCallback((msg: any) => {
    if (msg.type === "init") {
      setLiveTrack(msg.track ?? []);
    } else if (msg.type === "positions") {
      setLiveCars(msg.data ?? []);
      setLivePhase(msg.phase ?? "normal");
    }
  }, []);

  const { status: wsStatus } = useWebSocket(wsUrl, handleWsMessage);

  function startLive(session: Session, season: number, race: string) {
    setLiveSession(session);
    setLiveCars([]);
    setLiveTrack([]);
    const url = `${WS}/ws/${session.session_key}?season=${season}&race=${encodeURIComponent(race)}`;
    setWsUrl(url);
  }

  async function loadReplay() {
    setReplayLoading(true);
    setReplayError(null);
    setReplayPositions([]);
    try {
      // find the session key for this race
      const sRes = await fetch(`${API}/sessions?year=${replaySeason}&session_name=Race`);
      const sData: Session[] = await sRes.json();
      // replayRace is the exact circuit_short_name → exact match (no fuzzy false positives)
      const match = sData.find((s) => s.circuit_short_name === replayRace);
      if (!match) throw new Error(`No session found for ${replaySeason} ${replayRace}`);

      // /replay returns track outline + already-normalised positions together
      const rRes = await fetch(`${API}/replay/${match.session_key}`);
      if (!rRes.ok) {
        const err = await rRes.json().catch(() => ({}));
        throw new Error(err.detail ?? "Replay load failed");
      }
      const rData = await rRes.json();

      setReplayTrack(rData.track ?? []);
      setReplayDrivers(rData.drivers ?? {});
      setReplayPositions(
        (rData.positions ?? []).map((p: any) => ({
          driver: p.driver,
          x: p.x,
          y: p.y,
          acronym: rData.drivers?.[p.driver]?.acronym ?? "???",
          color: rData.drivers?.[p.driver]?.team_colour ?? "#AAA",
          date: p.date,
        }))
      );
    } catch (e: any) {
      setReplayError(e.message);
    } finally {
      setReplayLoading(false);
    }
  }

  const displayCars = mode === "live" ? liveCars : replay.currentPositions;
  const displayTrack = mode === "live" ? liveTrack : replayTrack;
  const displayPhase: RacePhase = mode === "live" ? livePhase : "normal";

  return (
    <div className="flex h-screen bg-gray-950 text-white overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 border-r border-gray-800 flex flex-col p-4 gap-4 flex-shrink-0 overflow-y-auto">
        <h1 className="text-base font-bold">🏎 F1 Tracker</h1>

        {/* Mode toggle */}
        <div className="flex rounded-lg overflow-hidden border border-gray-700 text-xs">
          {(["live", "replay"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-1.5 ${mode === m ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-400 hover:text-white"} transition-colors capitalize`}
            >
              {m}
            </button>
          ))}
        </div>

        {mode === "live" ? (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-gray-400">Recent races</p>
            {sessions.length === 0 && (
              <p className="text-xs text-gray-500">No recent race sessions found.</p>
            )}
            {sessions.slice(0, 8).map((s) => (
              <button
                key={s.session_key}
                onClick={() => startLive(s, s.year, s.circuit_short_name ?? "")}
                className={`text-left text-xs px-2 py-1.5 rounded border transition-colors ${
                  liveSession?.session_key === s.session_key
                    ? "border-blue-500 text-blue-300"
                    : "border-gray-700 text-gray-300 hover:border-gray-500"
                }`}
              >
                {s.year} {s.country_name}
                {liveSession?.session_key === s.session_key && (
                  <span className={`ml-1 text-xs ${wsStatus === "open" ? "text-green-400" : "text-yellow-400"}`}>
                    ● {wsStatus}
                  </span>
                )}
              </button>
            ))}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <p className="text-xs text-gray-400">Replay</p>
            <select
              value={replaySeason}
              onChange={(e) => setReplaySeason(Number(e.target.value))}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white focus:outline-none"
            >
              {REPLAY_SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <select
              value={replayRace}
              onChange={(e) => setReplayRace(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-white focus:outline-none"
            >
              {(REPLAY_RACES[replaySeason] ?? []).map((r) => (
                <option key={r.circuit} value={r.circuit}>{r.label}</option>
              ))}
            </select>
            <button
              onClick={loadReplay}
              disabled={replayLoading}
              className="py-1.5 text-xs bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 rounded transition-colors"
            >
              {replayLoading ? "Loading…" : "Load race"}
            </button>
            {replayError && <p className="text-red-400 text-xs">{replayError}</p>}

            {/* Replay controls */}
            {replayPositions.length > 0 && (
              <div className="flex flex-col gap-2 mt-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => replay.setPlaying((p) => !p)}
                    className="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded"
                  >
                    {replay.playing ? "⏸" : "▶"}
                  </button>
                  <select
                    value={replay.speed}
                    onChange={(e) => replay.setSpeed(Number(e.target.value))}
                    className="bg-gray-800 border border-gray-700 rounded px-1 py-0.5 text-xs text-white focus:outline-none"
                  >
                    {[1, 2, 5, 10].map((s) => <option key={s} value={s}>{s}×</option>)}
                  </select>
                </div>
                <input
                  type="range"
                  min={replay.minTime}
                  max={replay.maxTime}
                  value={replay.currentTime}
                  onChange={(e) => replay.setCurrentTime(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <p className="text-xs text-gray-500 text-center">
                  {Math.round(replay.progress * 100)}%
                </p>
              </div>
            )}
          </div>
        )}
      </aside>

      {/* Main area */}
      <div className="flex-1 flex gap-2 p-4 min-w-0">
        <div className="flex-1 bg-gray-900 rounded-xl overflow-hidden">
          <TrackSVG trackPath={displayTrack} cars={displayCars} phase={displayPhase} />
        </div>
        {displayCars.length > 0 && <TimingTower cars={displayCars} />}
      </div>
    </div>
  );
}
