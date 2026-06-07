import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "F1 Race Analyst",
  description: "AI-powered F1 race analysis with real timing data",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
