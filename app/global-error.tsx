"use client";

import * as Sentry from "@sentry/nextjs";
import { useEffect } from "react";

import "./globals.css";

export default function GlobalError({
  error,
}: {
  error: Error & { digest?: string };
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="en">
      <body>
        <main className="grid min-h-screen place-items-center px-5 text-center">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-lime">
              Something went wrong
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-ink">
              An unexpected error occurred
            </h1>
            <p className="mt-2 text-sm text-muted">
              We&apos;ve been notified. Try refreshing the page.
            </p>
          </div>
        </main>
      </body>
    </html>
  );
}
