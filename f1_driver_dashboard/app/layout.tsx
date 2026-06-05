import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "F1 Driver Dashboard",
  description: "Compare F1 drivers across seasons",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
