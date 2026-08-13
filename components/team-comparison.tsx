"use client";

import { useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type TeamAthlete = {
  user_id: string;
  display_name: string;
  consistency: { sessions_last_7_days: number; active_days_last_7_days: number };
  running: { weekly_distance_km: number };
  category_coverage: Record<string, number>;
};

type StationComparison = {
  exercise_key: string;
  exercise_name: string;
  metric: string | null;
  athlete_bests: Record<string, number>;
  stronger_user_id: string | null;
};

type TeamAnalytics = {
  athletes: TeamAthlete[];
  neglected_categories: string[];
  station_comparison: StationComparison[];
  shared_station_gaps: string[];
  joint_session_count: number;
  data_note: string | null;
};

type State =
  | { status: "loading" }
  | { status: "ready"; analytics: TeamAnalytics }
  | { status: "empty" }
  | { status: "error" };

function formatCategory(slug: string): string {
  return slug
    .split("_")
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(" ");
}

export function TeamComparison() {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/me", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const me = await response.json();
        const teamId: string | undefined = me.active_teams?.[0]?.id;
        if (!teamId) {
          setState({ status: "empty" });
          return;
        }
        const analyticsResponse = await authenticatedFetch(`/api/analytics/team/${teamId}`, {
          signal: controller.signal,
        });
        if (!analyticsResponse.ok) throw new Error();
        const analytics: TeamAnalytics = await analyticsResponse.json();
        setState({ status: "ready", analytics });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, []);

  if (state.status === "loading") return <div className="h-40 animate-pulse rounded-3xl bg-surface-2" />;
  if (state.status === "error" || state.status === "empty") return null;

  const {
    athletes,
    neglected_categories,
    station_comparison,
    shared_station_gaps,
    joint_session_count,
    data_note,
  } = state.analytics;
  if (athletes.length < 2) return null;

  const nameByUserId = Object.fromEntries(athletes.map((athlete) => [athlete.user_id, athlete.display_name]));

  return (
    <div className="rounded-3xl border border-line bg-surface p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Team</p>
      <h3 className="mt-2 text-sm font-semibold text-ink">How you compare</h3>
      <div className="mt-3 grid gap-4 sm:grid-cols-2">
        {athletes.map((athlete) => (
          <div key={athlete.user_id} className="rounded-2xl bg-surface-2 p-4">
            <p className="text-sm font-semibold text-ink">{athlete.display_name}</p>
            <p className="mt-1 text-xs text-muted">
              {athlete.consistency.sessions_last_7_days} sessions ·{" "}
              {athlete.running.weekly_distance_km.toFixed(1)} km running
            </p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs text-muted">
        {joint_session_count} joint session{joint_session_count === 1 ? "" : "s"} trained together
        this period.
      </p>
      {station_comparison.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">
            Station strengths
          </p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {station_comparison.map((station) => (
              <li key={station.exercise_key}>
                {station.exercise_name}:{" "}
                {station.stronger_user_id
                  ? `${nameByUserId[station.stronger_user_id] ?? "Athlete"} currently leads`
                  : "not enough shared data to compare yet"}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {neglected_categories.length > 0 ? (
        <p className="mt-4 text-sm text-muted">
          Neglected together: {neglected_categories.map(formatCategory).join(", ")}
        </p>
      ) : null}
      {shared_station_gaps.length > 0 ? (
        <p className="mt-2 text-sm text-muted">
          Neither of you has logged: {shared_station_gaps.map(formatCategory).join(", ")}
        </p>
      ) : null}
      {data_note ? <p className="mt-2 text-xs text-faint">{data_note}</p> : null}
    </div>
  );
}
