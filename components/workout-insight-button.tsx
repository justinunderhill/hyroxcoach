"use client";

import { useState } from "react";

import { CoachInsightCard } from "@/components/coach-insight-card";
import { CoachInsightResponse, generateWorkoutInsight } from "@/lib/coach";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; response: CoachInsightResponse }
  | { status: "error"; message: string };

export function WorkoutInsightButton({ workoutId }: { workoutId: string }) {
  const [state, setState] = useState<State>({ status: "idle" });

  async function handleClick() {
    setState({ status: "loading" });
    try {
      const response = await generateWorkoutInsight(workoutId);
      setState({ status: "ready", response });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "The insight could not be generated.",
      });
    }
  }

  if (state.status === "ready") {
    return (
      <div className="mt-3 rounded-2xl bg-stone-50 p-3">
        <CoachInsightCard insight={state.response.insight} />
      </div>
    );
  }

  return (
    <div className="mt-3">
      <button
        className="min-h-8 rounded-xl border border-stone-200 px-3 text-xs font-semibold text-stone-600 disabled:opacity-60"
        disabled={state.status === "loading"}
        onClick={handleClick}
        type="button"
      >
        {state.status === "loading" ? "Thinking…" : "Get coach insight"}
      </button>
      {state.status === "error" ? (
        <p className="mt-2 text-xs text-rose-700">{state.message}</p>
      ) : null}
    </div>
  );
}
