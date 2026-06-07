"use client";
import { CarPosition } from "@/types/tracker";

export function CarDot({ car, rank }: { car: CarPosition; rank: number }) {
  return (
    <g
      transform={`translate(${car.x}, ${car.y})`}
      style={{ transition: "transform 0.45s linear" }}
    >
      {/* Glow */}
      <circle r={11} fill={car.color} opacity={0.25} />
      {/* Body */}
      <circle r={7} fill={car.color} />
      {/* White border */}
      <circle r={7} fill="none" stroke="white" strokeWidth={1.5} />
      {/* Acronym label */}
      <text
        y={-13}
        textAnchor="middle"
        fill="white"
        fontSize={9}
        fontWeight="bold"
        style={{ textShadow: "0 1px 3px rgba(0,0,0,0.9)", pointerEvents: "none" }}
      >
        {car.acronym}
      </text>
    </g>
  );
}
