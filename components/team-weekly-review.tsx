"use client";

import { useEffect, useState } from "react";

import { CoachInsightCard } from "@/components/coach-insight-card";
import { authenticatedFetch } from "@/lib/auth/client";
import { CoachInsightResponse, getTeamWeeklyReview } from "@/lib/coach";

type State =
  | { status: "loading-team" }
  | { status: "no-team" }
  | { status: "idle"; teamId: string }
  | { status: "loading"; teamId: string }
  | { status: "ready"; teamId: string; response: CoachInsightResponse }
  | { status: "error"; teamId: string; message: string };

export function TeamWeeklyReview() {
  const [state, setState] = useState<State>({ status: "loading-team" });

  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/me", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const me = await response.json();
        const teamId: string | undefined = me.active_teams?.[0]?.id;
        setState(teamId ? { status: "idle", teamId } : { status: "no-team" });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "no-team" });
      });
    return () => controller.abort();
  }, []);

  async function handleGenerate(teamId: string) {
    setState({ status: "loading", teamId });
    try {
      const response = await getTeamWeeklyReview(teamId);
      setState({ status: "ready", teamId, response });
    } catch (error) {
      setState({
        status: "error",
        teamId,
        message:
          error instanceof Error ? error.message : "The team weekly review could not be generated.",
      });
    }
  }

  if (state.status === "loading-team" || state.status === "no-team") return null;

  return (
    <div className="rounded-3xl border border-line bg-surface p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Coach</p>
          <h3 className="mt-1 text-sm font-semibold text-ink">Team weekly review</h3>
        </div>
        {state.status !== "loading" ? (
          <button
            className="min-h-9 rounded-xl bg-lime px-3 text-xs font-bold text-lime-ink"
            onClick={() => handleGenerate(state.teamId)}
            type="button"
          >
            {state.status === "ready" ? "Refresh" : "Generate"}
          </button>
        ) : null}
      </div>

      {state.status === "loading" ? (
        <div className="mt-4 h-24 animate-pulse rounded-2xl bg-surface-2" />
      ) : null}
      {state.status === "error" ? (
        <p className="mt-4 rounded-2xl bg-red/10 px-4 py-3 text-sm text-red">{state.message}</p>
      ) : null}
      {state.status === "ready" ? (
        <div className="mt-4">
          <CoachInsightCard insight={state.response.insight} />
        </div>
      ) : null}
      {state.status === "idle" ? (
        <p className="mt-3 text-sm text-muted">
          Only team-visible activity is used — private workouts stay private, even in a shared review.
        </p>
      ) : null}
    </div>
  );
}
