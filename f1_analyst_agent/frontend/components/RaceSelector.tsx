"use client";
import { useState, useEffect } from "react";
import { getRaces } from "@/lib/api";

const SEASONS = [2024, 2023, 2022, 2021];

const EXAMPLE_QUESTIONS = [
  "Why did Verstappen win at Monza?",
  "Compare strategies in the 2023 Monaco GP",
  "Who had the best race pace in Silverstone?",
  "What happened with the safety car in Brazil?",
  "How did Hamilton recover from his grid penalty in Hungary?",
];

interface Props {
  onQuestion: (q: string) => void;
}

export function RaceSelector({ onQuestion }: Props) {
  const [season, setSeason] = useState(2023);
  const [races, setRaces] = useState<string[]>([]);
  const [race, setRace] = useState("");

  useEffect(() => {
    getRaces(season).then((r) => { setRaces(r); setRace(""); });
  }, [season]);

  function handleRaceSelect(r: string) {
    setRace(r);
  }

  function handleExample(q: string) {
    onQuestion(q);
  }

  function handleCustom() {
    if (!race) return;
    onQuestion(`Tell me about the ${season} ${race}`);
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Quick Race</p>
        <div className="flex gap-2">
          <select
            value={season}
            onChange={(e) => setSeason(Number(e.target.value))}
            className="bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-white flex-1 focus:outline-none"
          >
            {SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <select
          value={race}
          onChange={(e) => handleRaceSelect(e.target.value)}
          className="mt-2 w-full bg-gray-800 border border-gray-700 rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none"
        >
          <option value="">Select race…</option>
          {races.map((r) => <option key={r} value={r}>{r.replace(" Grand Prix", "")}</option>)}
        </select>
        <button
          onClick={handleCustom}
          disabled={!race}
          className="mt-2 w-full py-1.5 text-xs bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg transition-colors"
        >
          Analyse this race →
        </button>
      </div>

      <div>
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Example questions</p>
        <div className="flex flex-col gap-1.5">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => handleExample(q)}
              className="text-left text-xs text-gray-300 hover:text-white bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg px-3 py-2 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
