interface Props {
  label: string;
  valueA: string;
  valueB: string;
  colorA: string;
  colorB: string;
  better?: "A" | "B" | "none";
}

export function StatCard({ label, valueA, valueB, colorA, colorB, better }: Props) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-2">
      <p className="text-gray-400 text-xs font-semibold uppercase tracking-wide">{label}</p>
      <div className="flex justify-between items-center">
        <span
          className="text-2xl font-bold"
          style={{ color: colorA, filter: better === "A" ? "brightness(1.2)" : "brightness(0.8)" }}
        >
          {valueA}
          {better === "A" && <span className="text-sm ml-1">★</span>}
        </span>
        <span className="text-gray-500 text-sm">vs</span>
        <span
          className="text-2xl font-bold"
          style={{ color: colorB, filter: better === "B" ? "brightness(1.2)" : "brightness(0.8)" }}
        >
          {valueB}
          {better === "B" && <span className="text-sm ml-1">★</span>}
        </span>
      </div>
    </div>
  );
}
