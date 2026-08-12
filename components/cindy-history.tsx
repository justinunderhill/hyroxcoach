"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

type Attempt = {
  completed_at: string;
  full_rounds: number;
  total_reps: number;
  total_seconds: number;
  completed_as_prescribed: boolean;
};

type Change = {
  total_reps_change: number;
  total_seconds_change: number;
  full_rounds_change: number;
};

type CindyAnalytics = {
  latest: Attempt | null;
  personal_best: Attempt | null;
  change_from_previous: Change | null;
  history: Attempt[];
};

type HistoryState =
  | { status: "loading" }
  | { status: "ready"; analytics: CindyAnalytics }
  | { status: "error" };

export type CindyHistoryHandle = {
  refresh: () => void;
};

function formatClock(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export const CindyHistory = forwardRef<CindyHistoryHandle>(function CindyHistory(_props, ref) {
  const [state, setState] = useState<HistoryState>({ status: "loading" });
  const [reloadToken, setReloadToken] = useState(0);

  useImperativeHandle(ref, () => ({
    refresh: () => setReloadToken((token) => token + 1),
  }));

  useEffect(() => {
    const controller = new AbortController();
    setState({ status: "loading" });
    void authenticatedFetch("/api/analytics/cindy", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const analytics: CindyAnalytics = await response.json();
        setState({ status: "ready", analytics });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, [reloadToken]);

  if (state.status === "loading") return <div className="h-40 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error") {
    return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">Cindy history could not be loaded.</p>;
  }

  const { analytics } = state;

  if (!analytics.latest) {
    return (
      <div className="rounded-3xl border border-dashed border-stone-300 bg-white/50 p-6">
        <p className="text-sm text-stone-500">No Cindy attempts logged yet.</p>
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Cindy history</p>
      <div className="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{analytics.latest.total_reps}</p>
          <p className="text-xs text-stone-500">latest reps</p>
        </div>
        {analytics.personal_best ? (
          <div>
            <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{analytics.personal_best.total_reps}</p>
            <p className="text-xs text-stone-500">best reps</p>
          </div>
        ) : null}
        {analytics.change_from_previous ? (
          <div>
            <p className={`text-2xl font-semibold tracking-[-0.03em] ${analytics.change_from_previous.total_reps_change >= 0 ? "text-[#567118]" : "text-stone-500"}`}>
              {analytics.change_from_previous.total_reps_change >= 0 ? "+" : ""}
              {analytics.change_from_previous.total_reps_change}
            </p>
            <p className="text-xs text-stone-500">reps vs prior</p>
          </div>
        ) : null}
      </div>

      <ul className="mt-5 space-y-1.5 text-sm text-stone-600">
        {analytics.history.slice(0, 8).map((attempt) => (
          <li className="flex items-center justify-between" key={attempt.completed_at}>
            <span>
              {new Date(attempt.completed_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
              {attempt.completed_as_prescribed ? "" : " (early finish)"}
            </span>
            <span className="font-semibold text-stone-800">
              {attempt.full_rounds} rounds · {attempt.total_reps} reps · {formatClock(attempt.total_seconds)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
});
