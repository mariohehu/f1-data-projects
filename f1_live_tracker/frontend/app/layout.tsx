import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "F1 Live Car Tracker",
  description: "Real-time F1 car positions on circuit",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
