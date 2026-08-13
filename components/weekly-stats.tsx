"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type Analytics = {
  consistency: { sessions_last_7_days: number; active_days_last_7_days: number };
  category_coverage: Record<string, number>;
  race_demand_coverage: { trained_weight_pct: number; untrained_categories: string[] };
  running: {
    weekly_distance_km: number;
    avg_pace_seconds_per_km: number | null;
    best_5k_seconds: number | null;
  };
  simulation_history: {
    workout_id: string;
    occurred_at: string;
    total_duration_minutes: number | null;
  }[];
  data_note: string | null;
};

type StatsState =
  | { status: "loading" }
  | { status: "ready"; analytics: Analytics; displayName: string | null }
  | { status: "error" };

const MISSION_GROUPS: { label: string; slugs: string[]; target: number }[] = [
  { label: "Running", slugs: ["running"], target: 4 },
  { label: "Strength", slugs: ["strength", "mma_combat"], target: 3 },
  {
    label: "HYROX stations",
    slugs: [
      "skierg",
      "sled_push",
      "sled_pull",
      "burpee_broad_jumps",
      "row",
      "farmers_carry",
      "sandbag_lunges",
      "wall_balls",
    ],
    target: 4,
  },
  { label: "Mobility / recovery", slugs: ["mobility", "recovery", "walking"], target: 3 },
];

function formatPace(secondsPerKm: number | null): string {
  if (!secondsPerKm) return "—";
  const minutes = Math.floor(secondsPerKm / 60);
  const seconds = Math.round(secondsPerKm % 60)
    .toString()
    .padStart(2, "0");
  return `${minutes}:${seconds}/km`;
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 5) return "Still up";
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function trainingStatus(sessions: number): { label: string; tone: "lime" | "orange" | "muted" } {
  if (sessions >= 3) return { label: "On track", tone: "lime" };
  if (sessions >= 1) return { label: "Building", tone: "orange" };
  return { label: "Needs attention", tone: "muted" };
}

export function WeeklyStats() {
  const [state, setState] = useState<StatsState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([
      authenticatedFetch("/api/analytics/me", { signal: controller.signal }),
      authenticatedFetch("/api/me", { signal: controller.signal }),
    ])
      .then(async ([analyticsResponse, meResponse]) => {
        if (!analyticsResponse.ok) throw new Error();
        const analytics: Analytics = await analyticsResponse.json();
        const me = meResponse.ok ? await meResponse.json() : null;
        setState({
          status: "ready",
          analytics,
          displayName: me?.profile?.display_name ?? null,
        });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, []);

  if (state.status === "loading") {
    return (
      <div className="space-y-4">
        <div className="h-48 animate-pulse rounded-3xl bg-surface-2" />
        <div className="h-40 animate-pulse rounded-3xl bg-surface-2" />
      </div>
    );
  }
  if (state.status === "error") return null;

  const { analytics, displayName } = state;
  const status = trainingStatus(analytics.consistency.sessions_last_7_days);
  const categoriesCovered = Object.values(analytics.category_coverage).filter((count) => count > 0).length;
  const categoriesTotal = Object.keys(analytics.category_coverage).length;

  const toneClass = {
    lime: "bg-lime/15 text-lime",
    orange: "bg-orange/15 text-orange",
    muted: "bg-surface-2 text-muted",
  }[status.tone];

  return (
    <div className="space-y-4">
      <div className="rounded-3xl border border-line bg-surface p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">
              {greeting()}{displayName ? `, ${displayName.split(" ")[0]}` : ""}
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em] text-ink">Today&apos;s readiness</h2>
          </div>
          <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide ${toneClass}`}>
            {status.label}
          </span>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-3">
          <div className="rounded-2xl bg-surface-2 p-3">
            <p className="text-2xl font-bold tabular-nums tracking-[-0.03em] text-ink">{analytics.consistency.sessions_last_7_days}</p>
            <p className="text-[11px] text-faint">sessions this week</p>
          </div>
          <div className="rounded-2xl bg-surface-2 p-3">
            <p className="text-2xl font-bold tabular-nums tracking-[-0.03em] text-ink">{analytics.running.weekly_distance_km.toFixed(1)}</p>
            <p className="text-[11px] text-faint">km running</p>
          </div>
          <div className="rounded-2xl bg-surface-2 p-3">
            <p className="text-2xl font-bold tabular-nums tracking-[-0.03em] text-ink">{categoriesCovered}/{categoriesTotal}</p>
            <p className="text-[11px] text-faint">HYROX coverage</p>
          </div>
        </div>

        <p className="mt-4 text-xs text-muted">
          Avg pace {formatPace(analytics.running.avg_pace_seconds_per_km)} · Race-demand coverage{" "}
          {analytics.race_demand_coverage.trained_weight_pct}%
          {analytics.simulation_history.length > 0
            ? ` · ${analytics.simulation_history.length} simulation${analytics.simulation_history.length === 1 ? "" : "s"} logged`
            : ""}
        </p>
        {analytics.data_note ? <p className="mt-2 text-xs text-faint">{analytics.data_note}</p> : null}

        <Link
          className="mt-5 flex min-h-14 w-full items-center justify-center rounded-2xl bg-lime text-base font-black uppercase tracking-tight text-lime-ink"
          href="/workouts"
        >
          + Log activity
        </Link>
      </div>

      <div className="rounded-3xl border border-line bg-surface p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">This week&apos;s mission</p>
        <div className="mt-4 space-y-4">
          {MISSION_GROUPS.map((group) => {
            const count = group.slugs.reduce((sum, slug) => sum + (analytics.category_coverage[slug] ?? 0), 0);
            const pct = Math.min(100, Math.round((count / group.target) * 100));
            return (
              <div key={group.label}>
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-ink">{group.label}</span>
                  <span className="tabular-nums text-muted">{count}/{group.target}</span>
                </div>
                <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-2">
                  <div
                    className={`h-full rounded-full ${pct >= 100 ? "bg-green" : "bg-lime"}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
        <p className="mt-4 text-xs text-faint">Illustrative weekly aim — adjust to your own plan.</p>
      </div>
    </div>
  );
}
