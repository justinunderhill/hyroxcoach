"use client";

import { useState } from "react";

import { CoachInsightCard } from "@/components/coach-insight-card";
import { CoachInsightResponse, getWeeklyReview } from "@/lib/coach";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; response: CoachInsightResponse }
  | { status: "error"; message: string };

export function WeeklyReview() {
  const [state, setState] = useState<State>({ status: "idle" });

  async function handleGenerate() {
    setState({ status: "loading" });
    try {
      const response = await getWeeklyReview();
      setState({ status: "ready", response });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "The weekly review could not be generated.",
      });
    }
  }

  return (
    <div className="rounded-3xl border border-line bg-surface p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">Coach</p>
          <h3 className="mt-1 text-sm font-semibold text-ink">Your weekly review</h3>
        </div>
        {state.status !== "loading" ? (
          <button
            className="min-h-9 rounded-xl bg-lime px-3 text-xs font-bold text-lime-ink"
            onClick={handleGenerate}
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
          Get a grounded review of your last 7 days — consistency, running, stations and what to focus on next.
        </p>
      ) : null}
    </div>
  );
}
