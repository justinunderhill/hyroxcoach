import type { Metadata, Viewport } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "HYROX Coach",
  description: "Shared HYROX Doubles preparation, grounded in real training data.",
};

export const viewport: Viewport = {
  themeColor: "#15221b",
  colorScheme: "light",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
