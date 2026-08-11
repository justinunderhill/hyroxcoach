"use client";

import { useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type Analytics = {
  consistency: { sessions_last_7_days: number; active_days_last_7_days: number };
  category_coverage: Record<string, number>;
  running: {
    weekly_distance_km: number;
    avg_pace_seconds_per_km: number | null;
    best_5k_seconds: number | null;
  };
  data_note: string | null;
};

type StatsState =
  | { status: "loading" }
  | { status: "ready"; analytics: Analytics }
  | { status: "error" };

function formatPace(secondsPerKm: number | null): string {
  if (!secondsPerKm) return "—";
  const minutes = Math.floor(secondsPerKm / 60);
  const seconds = Math.round(secondsPerKm % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}/km`;
}

function formatDuration(totalSeconds: number | null): string {
  if (!totalSeconds) return "—";
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function WeeklyStats() {
  const [state, setState] = useState<StatsState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/analytics/me", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const analytics: Analytics = await response.json();
        setState({ status: "ready", analytics });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, []);

  if (state.status === "loading") return <div className="h-24 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error") return null;

  const { analytics } = state;
  const categoriesCovered = Object.values(analytics.category_coverage).filter((count) => count > 0).length;
  const categoriesTotal = Object.keys(analytics.category_coverage).length;

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">This week</p>
      <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{analytics.consistency.sessions_last_7_days}</p>
          <p className="text-xs text-stone-500">sessions</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{analytics.consistency.active_days_last_7_days}</p>
          <p className="text-xs text-stone-500">active days</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{analytics.running.weekly_distance_km.toFixed(1)}</p>
          <p className="text-xs text-stone-500">km running</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{categoriesCovered}/{categoriesTotal}</p>
          <p className="text-xs text-stone-500">categories covered</p>
        </div>
      </div>
      <p className="mt-4 text-sm text-stone-600">
        Avg pace {formatPace(analytics.running.avg_pace_seconds_per_km)}
        {analytics.running.best_5k_seconds ? ` · Best 5 km ${formatDuration(analytics.running.best_5k_seconds)}` : ""}
      </p>
      {analytics.data_note ? <p className="mt-2 text-xs text-stone-400">{analytics.data_note}</p> : null}
    </div>
  );
}
