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

type TeamAnalytics = {
  athletes: TeamAthlete[];
  neglected_categories: string[];
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

  if (state.status === "loading") return <div className="h-40 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error" || state.status === "empty") return null;

  const { athletes, neglected_categories, data_note } = state.analytics;
  if (athletes.length < 2) return null;

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Team</p>
      <h3 className="mt-2 text-sm font-semibold text-[#15221b]">How you compare</h3>
      <div className="mt-3 grid gap-4 sm:grid-cols-2">
        {athletes.map((athlete) => (
          <div key={athlete.user_id} className="rounded-2xl bg-stone-50 p-4">
            <p className="text-sm font-semibold text-[#15221b]">{athlete.display_name}</p>
            <p className="mt-1 text-xs text-stone-500">
              {athlete.consistency.sessions_last_7_days} sessions ·{" "}
              {athlete.running.weekly_distance_km.toFixed(1)} km running
            </p>
          </div>
        ))}
      </div>
      {neglected_categories.length > 0 ? (
        <p className="mt-4 text-sm text-stone-600">
          Neglected together: {neglected_categories.map(formatCategory).join(", ")}
        </p>
      ) : null}
      {data_note ? <p className="mt-2 text-xs text-stone-400">{data_note}</p> : null}
    </div>
  );
}
