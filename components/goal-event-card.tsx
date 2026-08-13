"use client";

import { FormEvent, useEffect, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";
import { getGoalEvent, GoalEvent, upsertGoalEvent } from "@/lib/goal-event";

type State =
  | { status: "loading-team" }
  | { status: "no-team" }
  | { status: "loading"; teamId: string }
  | { status: "ready"; teamId: string; goalEvent: GoalEvent | null }
  | { status: "editing"; teamId: string; goalEvent: GoalEvent | null }
  | { status: "error"; teamId: string; message: string };

export function GoalEventCard() {
  const [state, setState] = useState<State>({ status: "loading-team" });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/me", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error();
        const me = await response.json();
        const teamId: string | undefined = me.active_teams?.[0]?.id;
        if (!teamId) {
          setState({ status: "no-team" });
          return;
        }
        setState({ status: "loading", teamId });
        const goalEvent = await getGoalEvent(teamId, controller.signal);
        setState({ status: "ready", teamId, goalEvent });
      })
      .catch((fetchError: unknown) => {
        if (fetchError instanceof DOMException && fetchError.name === "AbortError") return;
        setState({ status: "no-team" });
      });
    return () => controller.abort();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (state.status !== "editing") return;
    setError(null);
    setIsSubmitting(true);

    const data = new FormData(event.currentTarget);
    try {
      const goalEvent = await upsertGoalEvent(state.teamId, {
        name: String(data.get("name") ?? "").trim(),
        event_date: String(data.get("eventDate") ?? ""),
        division: String(data.get("division") ?? "").trim() || null,
        location: String(data.get("location") ?? "").trim() || null,
      });
      setState({ status: "ready", teamId: state.teamId, goalEvent });
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "The target event could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  if (state.status === "loading-team" || state.status === "no-team") return null;
  if (state.status === "loading") {
    return <div className="h-28 animate-pulse rounded-3xl bg-surface-2" />;
  }

  if (state.status === "editing") {
    const goalEvent = state.goalEvent;
    return (
      <div className="rounded-3xl border border-lime/30 bg-lime/10 p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Target event</p>
        <form className="mt-3 space-y-3" onSubmit={handleSubmit}>
          <label className="block text-sm font-semibold text-ink">
            Event name
            <input
              className="mt-1 min-h-11 w-full rounded-xl border border-lime/30 px-3 text-sm"
              defaultValue={goalEvent?.name}
              maxLength={120}
              name="name"
              placeholder="HYROX Doubles London"
              required
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-xs font-semibold text-lime">
              Race date
              <input
                className="mt-1 min-h-11 w-full rounded-xl border border-lime/30 px-3 text-sm"
                defaultValue={goalEvent?.event_date}
                name="eventDate"
                required
                type="date"
              />
            </label>
            <label className="block text-xs font-semibold text-lime">
              Division
              <input
                className="mt-1 min-h-11 w-full rounded-xl border border-lime/30 px-3 text-sm"
                defaultValue={goalEvent?.division ?? ""}
                maxLength={80}
                name="division"
                placeholder="Open"
              />
            </label>
          </div>
          <label className="block text-xs font-semibold text-lime">
            Location <span className="font-normal text-faint">(optional)</span>
            <input
              className="mt-1 min-h-11 w-full rounded-xl border border-lime/30 px-3 text-sm"
              defaultValue={goalEvent?.location ?? ""}
              maxLength={120}
              name="location"
            />
          </label>
          {error ? <p className="rounded-xl bg-red/10 px-3 py-2 text-xs text-red">{error}</p> : null}
          <div className="flex gap-2">
            <button
              className="min-h-10 rounded-xl bg-lime px-4 text-xs font-bold text-lime-ink disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? "Saving…" : "Save target event"}
            </button>
            <button
              className="min-h-10 rounded-xl border border-line-strong px-4 text-xs font-semibold text-ink"
              onClick={() => setState({ status: "ready", teamId: state.teamId, goalEvent })}
              type="button"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  }

  if (state.status === "error") {
    return <p className="rounded-3xl bg-red/10 p-6 text-sm text-red">{state.message}</p>;
  }

  const { goalEvent, teamId } = state;

  if (goalEvent) {
    return (
      <div className="rounded-3xl border border-lime/20 bg-gradient-to-br from-lime/10 to-surface p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{goalEvent.name}</p>
            <p className="mt-1 font-mono text-5xl font-black tabular-nums leading-none text-lime sm:text-6xl">
              {Math.abs(goalEvent.days_until_event)}
            </p>
            <p className="mt-1 text-xs font-bold uppercase tracking-[0.2em] text-muted">
              {goalEvent.days_until_event < 0 ? "days ago" : goalEvent.days_until_event === 0 ? "race day" : "days to race"}
            </p>
          </div>
          <button
            className="min-h-9 shrink-0 rounded-xl border border-line-strong px-3 text-xs font-semibold text-ink"
            onClick={() => setState({ status: "editing", teamId, goalEvent })}
            type="button"
          >
            Edit
          </button>
        </div>
        {goalEvent.division || goalEvent.location ? (
          <p className="mt-3 text-xs text-muted">
            {[goalEvent.division, goalEvent.location].filter(Boolean).join(" · ")}
          </p>
        ) : null}
        {goalEvent.is_taper_week ? (
          <p className="mt-3 rounded-xl bg-surface-2 px-3 py-2 text-xs font-semibold text-lime">
            Race week — this is taper time. Prioritize freshness over volume.
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="rounded-3xl border border-lime/30 bg-lime/10 p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Target event</p>
      <p className="mt-2 text-sm leading-6 text-muted">
        No target race set yet. Add one so the coach can talk about race countdown.
      </p>
      <button
        className="mt-4 min-h-9 rounded-xl border border-line-strong px-3 text-xs font-semibold text-ink"
        onClick={() => setState({ status: "editing", teamId, goalEvent })}
        type="button"
      >
        Set target event
      </button>
    </div>
  );
}
