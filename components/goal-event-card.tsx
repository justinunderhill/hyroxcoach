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

function daysUntilLabel(days: number): string {
  if (days < 0) return `${Math.abs(days)} days ago`;
  if (days === 0) return "Today";
  return `${days} days to go`;
}

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
    return <div className="h-28 animate-pulse rounded-3xl bg-stone-100" />;
  }

  if (state.status === "editing") {
    const goalEvent = state.goalEvent;
    return (
      <div className="rounded-3xl border border-[#dbe998] bg-[#f8ffe4] p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Target event</p>
        <form className="mt-3 space-y-3" onSubmit={handleSubmit}>
          <label className="block text-sm font-semibold text-[#263711]">
            Event name
            <input
              className="mt-1 min-h-11 w-full rounded-xl border border-[#c7dd7a] px-3 text-sm"
              defaultValue={goalEvent?.name}
              maxLength={120}
              name="name"
              placeholder="HYROX Doubles London"
              required
            />
          </label>
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-xs font-semibold text-[#567118]">
              Race date
              <input
                className="mt-1 min-h-11 w-full rounded-xl border border-[#c7dd7a] px-3 text-sm"
                defaultValue={goalEvent?.event_date}
                name="eventDate"
                required
                type="date"
              />
            </label>
            <label className="block text-xs font-semibold text-[#567118]">
              Division
              <input
                className="mt-1 min-h-11 w-full rounded-xl border border-[#c7dd7a] px-3 text-sm"
                defaultValue={goalEvent?.division ?? ""}
                maxLength={80}
                name="division"
                placeholder="Open"
              />
            </label>
          </div>
          <label className="block text-xs font-semibold text-[#567118]">
            Location <span className="font-normal text-stone-400">(optional)</span>
            <input
              className="mt-1 min-h-11 w-full rounded-xl border border-[#c7dd7a] px-3 text-sm"
              defaultValue={goalEvent?.location ?? ""}
              maxLength={120}
              name="location"
            />
          </label>
          {error ? <p className="rounded-xl bg-rose-50 px-3 py-2 text-xs text-rose-800">{error}</p> : null}
          <div className="flex gap-2">
            <button
              className="min-h-10 rounded-xl bg-[#15271e] px-4 text-xs font-bold text-white disabled:opacity-60"
              disabled={isSubmitting}
              type="submit"
            >
              {isSubmitting ? "Saving…" : "Save target event"}
            </button>
            <button
              className="min-h-10 rounded-xl border border-[#263711]/20 px-4 text-xs font-semibold text-[#263711]"
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
    return <p className="rounded-3xl bg-rose-50 p-6 text-sm text-rose-800">{state.message}</p>;
  }

  const { goalEvent, teamId } = state;

  return (
    <div className="rounded-3xl border border-[#dbe998] bg-[#f8ffe4] p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-500">Target event</p>
      {goalEvent ? (
        <>
          <h3 className="mt-2 text-xl font-semibold text-[#263711]">{goalEvent.name}</h3>
          <p className="mt-1 text-sm text-[#567118]">
            {new Date(goalEvent.event_date).toLocaleDateString(undefined, { dateStyle: "long" })} ·{" "}
            {daysUntilLabel(goalEvent.days_until_event)}
          </p>
          {goalEvent.division || goalEvent.location ? (
            <p className="mt-1 text-xs text-stone-500">
              {[goalEvent.division, goalEvent.location].filter(Boolean).join(" · ")}
            </p>
          ) : null}
          {goalEvent.is_taper_week ? (
            <p className="mt-3 rounded-xl bg-[#263711] px-3 py-2 text-xs font-semibold text-[#d8ff62]">
              Race week — this is taper time. Prioritize freshness over volume.
            </p>
          ) : null}
        </>
      ) : (
        <p className="mt-2 text-sm leading-6 text-stone-600">
          No target race set yet. Add one so the coach can talk about race countdown.
        </p>
      )}
      <button
        className="mt-4 min-h-9 rounded-xl border border-[#263711]/20 px-3 text-xs font-semibold text-[#263711]"
        onClick={() => setState({ status: "editing", teamId, goalEvent })}
        type="button"
      >
        {goalEvent ? "Edit target event" : "Set target event"}
      </button>
    </div>
  );
}
