"use client";

import { useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type MetricType = "load_kg" | "duration_seconds" | "distance_m" | "reps";

type PersonalBest = {
  exercise_key: string;
  exercise_name: string;
  metric: MetricType;
  best_value: number;
  achieved_at: string;
  is_current: boolean;
};

type ProgressionPoint = {
  occurred_at: string;
  load_kg: number | null;
  reps: number | null;
  duration_seconds: number | null;
  distance_m: number | null;
};

type Progression = {
  exercise_key: string;
  exercise_name: string;
  primary_metric: MetricType;
  trend: "improving" | "flat" | "declining" | null;
  points: ProgressionPoint[];
};

type Analytics = {
  station_history: Progression[];
  personal_bests: PersonalBest[];
};

type State = { status: "loading" } | { status: "ready"; analytics: Analytics } | { status: "error" };

function formatMetric(metric: MetricType, value: number): string {
  switch (metric) {
    case "load_kg":
      return `${value} kg`;
    case "duration_seconds": {
      const minutes = Math.floor(value / 60);
      const seconds = Math.round(value % 60)
        .toString()
        .padStart(2, "0");
      return `${minutes}:${seconds}`;
    }
    case "distance_m":
      return `${value} m`;
    default:
      return `${value} reps`;
  }
}

function trendLabel(trend: Progression["trend"]): string {
  if (trend === "improving") return "Improving";
  if (trend === "declining") return "Declining";
  if (trend === "flat") return "Holding steady";
  return "Not enough data yet";
}

export function ExerciseProgress() {
  const [state, setState] = useState<State>({ status: "loading" });

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

  if (state.status === "loading") return <div className="h-40 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error") return null;

  const { station_history, personal_bests } = state.analytics;
  if (station_history.length === 0 && personal_bests.length === 0) return null;

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Progression</p>
      {personal_bests.length > 0 ? (
        <div className="mt-3">
          <h3 className="text-sm font-semibold text-[#15221b]">Personal bests</h3>
          <ul className="mt-2 space-y-1.5">
            {personal_bests.slice(0, 6).map((best) => (
              <li key={best.exercise_key} className="flex items-center justify-between text-sm">
                <span className="text-stone-600">{best.exercise_name}</span>
                <span className="font-semibold text-[#15221b]">
                  {formatMetric(best.metric, best.best_value)}
                  {best.is_current ? <span className="ml-2 text-xs font-bold text-[#3c6b2f]">PB</span> : null}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {station_history.length > 0 ? (
        <div className="mt-5">
          <h3 className="text-sm font-semibold text-[#15221b]">HYROX stations</h3>
          <ul className="mt-2 space-y-1.5">
            {station_history.map((station) => (
              <li key={station.exercise_key} className="flex items-center justify-between text-sm">
                <span className="text-stone-600">{station.exercise_name}</span>
                <span className="text-xs text-stone-500">{trendLabel(station.trend)}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
