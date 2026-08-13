"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import { authenticatedFetch } from "@/lib/auth/client";

const FULL_DURATION_MS = 1_200_000;

type Phase = "idle" | "running" | "paused" | "finished";

function formatClock(ms: number): string {
  const totalSeconds = Math.max(0, Math.round(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

type CindyTimerProps = {
  onCompleted: () => void;
};

export function CindyTimer({ onCompleted }: CindyTimerProps) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [accumulatedMs, setAccumulatedMs] = useState(0);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [fullRounds, setFullRounds] = useState(0);
  const [extraPullups, setExtraPullups] = useState(0);
  const [extraPushups, setExtraPushups] = useState(0);
  const [extraSquats, setExtraSquats] = useState(0);
  const [finalSeconds, setFinalSeconds] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const capHit = useRef(false);

  useEffect(() => {
    if (phase !== "running") return;
    const interval = setInterval(() => setNow(Date.now()), 250);
    return () => clearInterval(interval);
  }, [phase]);

  const liveElapsedMs =
    phase === "running" && startedAt !== null ? accumulatedMs + (now - startedAt) : accumulatedMs;

  useEffect(() => {
    if (phase === "running" && liveElapsedMs >= FULL_DURATION_MS && !capHit.current) {
      capHit.current = true;
      setAccumulatedMs(FULL_DURATION_MS);
      setPhase("paused");
    }
  }, [phase, liveElapsedMs]);

  function handleStart() {
    void authenticatedFetch("/api/workouts/cindy/start", { method: "POST" }).catch(() => {});
    setStartedAt(Date.now());
    setPhase("running");
  }

  function handlePause() {
    setAccumulatedMs(liveElapsedMs);
    setStartedAt(null);
    setPhase("paused");
  }

  function handleResume() {
    setStartedAt(Date.now());
    setPhase("running");
  }

  function handleFinish() {
    const elapsed = Math.min(FULL_DURATION_MS, liveElapsedMs);
    setAccumulatedMs(elapsed);
    setStartedAt(null);
    setFinalSeconds(Math.max(1, Math.round(elapsed / 1000)));
    setPhase("finished");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (finalSeconds === null) return;
    setError(null);
    setIsSubmitting(true);

    const data = new FormData(event.currentTarget);
    const rpe = data.get("rpe") ? Number(data.get("rpe")) : null;
    const notes = String(data.get("notes") ?? "").trim() || null;
    const visibility = String(data.get("visibility") ?? "team");
    const caloriesBurned = data.get("caloriesBurned") ? Number(data.get("caloriesBurned")) : null;
    const estimateCalories = data.get("estimateCalories") === "on";

    try {
      const response = await authenticatedFetch("/api/workouts/cindy/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          total_seconds: finalSeconds,
          full_rounds: fullRounds,
          extra_pullups: extraPullups,
          extra_pushups: extraPushups,
          extra_squats: extraSquats,
          rpe,
          notes,
          visibility,
          calories_burned: caloriesBurned,
          estimate_calories: estimateCalories,
        }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        const message = body?.error?.message;
        throw new Error(typeof message === "string" ? message : "Your Cindy result could not be saved.");
      }

      setPhase("idle");
      setAccumulatedMs(0);
      setStartedAt(null);
      setFullRounds(0);
      setExtraPullups(0);
      setExtraPushups(0);
      setExtraSquats(0);
      setFinalSeconds(null);
      capHit.current = false;
      onCompleted();
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Your Cindy result could not be saved.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const remainingMs = Math.max(0, FULL_DURATION_MS - liveElapsedMs);
  const totalRounds = fullRounds;

  if (phase === "finished") {
    return (
      <div className="rounded-3xl border border-line bg-surface p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-faint">20-minute AMRAP</p>
        <p className="mt-2 text-sm text-muted">5 pull-ups, 10 push-ups, 15 air squats — repeat.</p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <p className="text-center text-sm text-muted">
            {fullRounds} full rounds · {extraPullups + extraPushups + extraSquats} partial reps · {formatClock((finalSeconds ?? 0) * 1000)} elapsed
          </p>

          <div className="grid grid-cols-2 gap-3">
            <label className="text-xs font-semibold text-muted">
              RPE <span className="font-normal text-faint">(optional)</span>
              <input className="mt-1 min-h-12 w-full rounded-2xl border border-line-strong bg-surface-2 px-4 text-base text-ink" max={10} min={1} name="rpe" type="number" />
            </label>
            <label className="text-xs font-semibold text-muted">
              Calories <span className="font-normal text-faint">(from device)</span>
              <input className="mt-1 min-h-12 w-full rounded-2xl border border-line-strong bg-surface-2 px-4 text-base text-ink" min={0} name="caloriesBurned" type="number" />
            </label>
          </div>

          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-line bg-surface-2 px-3 text-sm text-ink">
            <input className="accent-lime" name="estimateCalories" type="checkbox" />
            No device reading — estimate calories for me
          </label>

          <fieldset>
            <legend className="text-sm font-semibold text-ink">Visibility</legend>
            <div className="mt-2 flex gap-3">
              <label className="flex min-h-11 items-center gap-2 rounded-xl border border-line bg-surface-2 px-3 text-sm text-ink">
                <input defaultChecked className="accent-lime" name="visibility" type="radio" value="team" />
                Share with team
              </label>
              <label className="flex min-h-11 items-center gap-2 rounded-xl border border-line bg-surface-2 px-3 text-sm text-ink">
                <input className="accent-lime" name="visibility" type="radio" value="private" />
                Private
              </label>
            </div>
          </fieldset>

          <label className="block text-sm font-semibold text-ink">
            Notes <span className="font-normal text-faint">(optional)</span>
            <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-line-strong bg-surface-2 px-4 py-3 text-base text-ink" maxLength={2000} name="notes" />
          </label>

          {error ? <p aria-live="polite" className="rounded-2xl bg-red/10 px-4 py-3 text-sm text-red">{error}</p> : null}

          <button
            className="min-h-12 w-full rounded-2xl bg-lime px-5 py-3 text-sm font-bold text-lime-ink disabled:cursor-wait disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Saving…" : "Save result"}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="flex min-h-[calc(100vh-2rem)] flex-col rounded-3xl bg-canvas p-6 sm:min-h-[36rem]">
      <div className="text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-faint">20-minute AMRAP</p>
        <p className="mt-1 text-sm text-muted">5 pull-ups · 10 push-ups · 15 air squats — repeat</p>
      </div>

      <div className="flex flex-1 flex-col items-center justify-center">
        <p className="font-mono text-7xl font-bold tabular-nums text-ink sm:text-8xl">
          {formatClock(remainingMs)}
        </p>
        <p className="mt-3 text-sm font-semibold uppercase tracking-[0.3em] text-lime">
          Round {totalRounds + 1}
        </p>

        <div className="mt-6 flex justify-center gap-3">
          {phase === "idle" ? (
            <button className="min-h-12 rounded-2xl bg-lime px-8 text-sm font-bold text-lime-ink" onClick={handleStart} type="button">
              Start
            </button>
          ) : null}
          {phase === "running" ? (
            <button className="min-h-12 rounded-2xl border border-line-strong px-8 text-sm font-semibold text-ink" onClick={handlePause} type="button">
              Pause
            </button>
          ) : null}
          {phase === "paused" ? (
            <button className="min-h-12 rounded-2xl bg-lime px-8 text-sm font-bold text-lime-ink" onClick={handleResume} type="button">
              Resume
            </button>
          ) : null}
          {phase !== "idle" ? (
            <button className="min-h-12 rounded-2xl border border-line-strong px-8 text-sm font-semibold text-ink" onClick={handleFinish} type="button">
              Finish
            </button>
          ) : null}
        </div>
      </div>

      <div className="flex flex-col items-center gap-3">
        <button
          className="min-h-16 w-full max-w-sm rounded-3xl bg-lime text-xl font-black uppercase tracking-tight text-lime-ink shadow-[0_0_40px_rgba(200,255,61,0.25)] disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
          disabled={phase === "idle"}
          onClick={() => setFullRounds((value) => value + 1)}
          type="button"
        >
          Round complete · {fullRounds}
        </button>
        <button
          className="min-h-10 w-full max-w-sm rounded-xl border border-line-strong bg-surface text-xs font-semibold text-muted disabled:opacity-40"
          disabled={phase === "idle" || fullRounds === 0}
          onClick={() => setFullRounds((value) => Math.max(0, value - 1))}
          type="button"
        >
          − Undo round
        </button>
        <div className="grid w-full max-w-sm grid-cols-3 gap-2">
          <div className="flex min-h-11 items-center justify-between rounded-xl border border-line bg-surface px-2 text-xs font-semibold text-ink">
            <button
              aria-label="Decrease pull-ups"
              className="min-h-8 min-w-8 rounded-lg text-muted disabled:opacity-30"
              disabled={phase === "idle" || extraPullups === 0}
              onClick={() => setExtraPullups((v) => Math.max(0, v - 1))}
              type="button"
            >
              −
            </button>
            <span className="px-1 text-center">Pull-ups ({extraPullups})</span>
            <button
              aria-label="Increase pull-ups"
              className="min-h-8 min-w-8 rounded-lg text-muted disabled:opacity-30"
              disabled={phase === "idle"}
              onClick={() => setExtraPullups((v) => v + 1)}
              type="button"
            >
              +
            </button>
          </div>
          <div className="flex min-h-11 items-center justify-between rounded-xl border border-line bg-surface px-2 text-xs font-semibold text-ink">
            <button
              aria-label="Decrease push-ups"
              className="min-h-8 min-w-8 rounded-lg text-muted disabled:opacity-30"
              disabled={phase === "idle" || extraPushups === 0}
              onClick={() => setExtraPushups((v) => Math.max(0, v - 1))}
              type="button"
            >
              −
            </button>
            <span className="px-1 text-center">Push-ups ({extraPushups})</span>
            <button
              aria-label="Increase push-ups"
              className="min-h-8 min-w-8 rounded-lg text-muted disabled:opacity-30"
              disabled={phase === "idle"}
              onClick={() => setExtraPushups((v) => v + 1)}
              type="button"
            >
              +
            </button>
          </div>
          <div className="flex min-h-11 items-center justify-between rounded-xl border border-line bg-surface px-2 text-xs font-semibold text-ink">
            <button
              aria-label="Decrease squats"
              className="min-h-8 min-w-8 rounded-lg text-muted disabled:opacity-30"
              disabled={phase === "idle" || extraSquats === 0}
              onClick={() => setExtraSquats((v) => Math.max(0, v - 1))}
              type="button"
            >
              −
            </button>
            <span className="px-1 text-center">Squats ({extraSquats})</span>
            <button
              aria-label="Increase squats"
              className="min-h-8 min-w-8 rounded-lg text-muted disabled:opacity-30"
              disabled={phase === "idle"}
              onClick={() => setExtraSquats((v) => v + 1)}
              type="button"
            >
              +
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
