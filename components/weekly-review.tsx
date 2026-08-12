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
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Coach</p>
          <h3 className="mt-1 text-sm font-semibold text-[#15221b]">Your weekly review</h3>
        </div>
        {state.status !== "loading" ? (
          <button
            className="min-h-9 rounded-xl bg-[#15271e] px-3 text-xs font-bold text-white"
            onClick={handleGenerate}
            type="button"
          >
            {state.status === "ready" ? "Refresh" : "Generate"}
          </button>
        ) : null}
      </div>

      {state.status === "loading" ? (
        <div className="mt-4 h-24 animate-pulse rounded-2xl bg-stone-100" />
      ) : null}
      {state.status === "error" ? (
        <p className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{state.message}</p>
      ) : null}
      {state.status === "ready" ? (
        <div className="mt-4">
          <CoachInsightCard insight={state.response.insight} />
        </div>
      ) : null}
      {state.status === "idle" ? (
        <p className="mt-3 text-sm text-stone-500">
          Get a grounded review of your last 7 days — consistency, running, stations and what to focus on next.
        </p>
      ) : null}
    </div>
  );
}
