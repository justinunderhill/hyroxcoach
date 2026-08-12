"use client";

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";

import { authClient, authenticatedFetch } from "@/lib/auth/client";

type StepsEntry = {
  id: string;
  user_id: string;
  date: string;
  steps: number;
  source: string;
  visibility: "team" | "private";
};

type StepsHistory = {
  entries: StepsEntry[];
  weekly_total: number;
  seven_day_average: number;
  trend_vs_prior_week: number;
};

type SummaryState =
  | { status: "loading" }
  | { status: "ready"; history: StepsHistory }
  | { status: "error" };

export type StepsSummaryHandle = {
  refresh: () => void;
};

export const StepsSummary = forwardRef<StepsSummaryHandle>(function StepsSummary(_props, ref) {
  const { data: session } = authClient.useSession();
  const [state, setState] = useState<SummaryState>({ status: "loading" });
  const [reloadToken, setReloadToken] = useState(0);
  const [deletingDate, setDeletingDate] = useState<string | null>(null);
  const [deleteErrorDate, setDeleteErrorDate] = useState<string | null>(null);

  useImperativeHandle(ref, () => ({
    refresh: () => setReloadToken((token) => token + 1),
  }));

  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/steps", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const history: StepsHistory = await response.json();
        setState({ status: "ready", history });
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setState({ status: "error" });
      });
    return () => controller.abort();
  }, [reloadToken]);

  async function handleDelete(date: string) {
    if (!window.confirm("Delete this day's steps? This cannot be undone.")) return;
    setDeleteErrorDate(null);
    setDeletingDate(date);
    try {
      const response = await authenticatedFetch(`/api/steps/${date}`, { method: "DELETE" });
      if (!response.ok && response.status !== 204) {
        throw new Error("This entry could not be deleted.");
      }
      setReloadToken((token) => token + 1);
    } catch {
      setDeleteErrorDate(date);
    } finally {
      setDeletingDate(null);
    }
  }

  if (state.status === "loading") return <div className="h-48 animate-pulse rounded-3xl bg-stone-100" />;
  if (state.status === "error") {
    return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">Step history could not be loaded.</p>;
  }

  const { history } = state;
  const trend = history.trend_vs_prior_week;
  const currentUserId = session?.user?.id;

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">Steps</p>
      <div className="mt-3 grid grid-cols-3 gap-4">
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{history.weekly_total.toLocaleString()}</p>
          <p className="text-xs text-stone-500">7-day total</p>
        </div>
        <div>
          <p className="text-2xl font-semibold tracking-[-0.03em] text-[#15221b]">{history.seven_day_average.toLocaleString()}</p>
          <p className="text-xs text-stone-500">7-day average</p>
        </div>
        <div>
          <p className={`text-2xl font-semibold tracking-[-0.03em] ${trend >= 0 ? "text-[#567118]" : "text-stone-500"}`}>
            {trend >= 0 ? "+" : ""}
            {trend.toLocaleString()}
          </p>
          <p className="text-xs text-stone-500">vs prior week</p>
        </div>
      </div>

      {history.entries.length > 0 ? (
        <ul className="mt-5 space-y-1.5 text-sm text-stone-600">
          {history.entries.slice(0, 7).map((entry) => {
            const isOwner = currentUserId !== undefined && entry.user_id === currentUserId;
            return (
              <li className="flex items-center justify-between gap-3" key={entry.id}>
                <span>{new Date(entry.date).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })}</span>
                <span className="flex items-center gap-2">
                  <span className="font-semibold text-stone-800">{entry.steps.toLocaleString()}</span>
                  {isOwner ? (
                    <button
                      className="text-xs font-semibold text-rose-700 underline decoration-rose-300 underline-offset-4 disabled:opacity-50"
                      disabled={deletingDate === entry.date}
                      onClick={() => handleDelete(entry.date)}
                      type="button"
                    >
                      {deletingDate === entry.date ? "Deleting…" : "Delete"}
                    </button>
                  ) : null}
                </span>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="mt-5 text-sm text-stone-500">No steps logged yet.</p>
      )}
      {deleteErrorDate ? (
        <p className="mt-2 text-xs text-rose-700">That entry could not be deleted.</p>
      ) : null}
    </div>
  );
});
