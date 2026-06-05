"use client";
import { useState, useEffect } from "react";

interface Driver {
  driverId: string;
  displayName: string;
}

interface Props {
  season: number;
  label: string;
  value: Driver | null;
  onChange: (d: Driver | null) => void;
}

export function DriverSelector({ season, label, value, onChange }: Props) {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    setLoading(true);
    fetch(`/api/drivers?season=${season}`)
      .then((r) => r.json())
      .then((data) => { setDrivers(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [season]);

  const filtered = drivers.filter((d) =>
    d.displayName.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-semibold text-gray-300">{label}</label>
      <input
        type="text"
        placeholder="Search driver..."
        value={query}
        onChange={(e) => { setQuery(e.target.value); onChange(null); }}
        className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-400"
      />
      {loading && <p className="text-xs text-gray-400">Loading...</p>}
      {query && (
        <ul className="bg-gray-800 border border-gray-600 rounded max-h-48 overflow-y-auto">
          {filtered.map((d) => (
            <li
              key={d.driverId}
              onClick={() => { onChange(d); setQuery(d.displayName); }}
              className={`px-3 py-2 cursor-pointer text-sm hover:bg-gray-700 ${
                value?.driverId === d.driverId ? "bg-gray-700 text-blue-400" : "text-white"
              }`}
            >
              {d.displayName}
            </li>
          ))}
          {filtered.length === 0 && <li className="px-3 py-2 text-gray-400 text-sm">No results</li>}
        </ul>
      )}
      {value && (
        <p className="text-xs text-green-400">Selected: {value.displayName} ({value.driverId})</p>
      )}
    </div>
  );
}
