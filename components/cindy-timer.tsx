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

  return (
    <div className="rounded-3xl border border-stone-200 bg-white p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">20-minute AMRAP</p>
      <p className="mt-2 text-sm text-stone-500">5 pull-ups, 10 push-ups, 15 air squats — repeat.</p>

      <p className="mt-6 text-center font-mono text-6xl font-bold tabular-nums text-[#15221b]">
        {formatClock(remainingMs)}
      </p>

      {phase !== "finished" ? (
        <>
          <div className="mt-6 flex justify-center gap-3">
            {phase === "idle" ? (
              <button className="min-h-12 rounded-2xl bg-[#15271e] px-6 text-sm font-bold text-white" onClick={handleStart} type="button">
                Start
              </button>
            ) : null}
            {phase === "running" ? (
              <button className="min-h-12 rounded-2xl border border-stone-300 px-6 text-sm font-semibold text-stone-700" onClick={handlePause} type="button">
                Pause
              </button>
            ) : null}
            {phase === "paused" ? (
              <button className="min-h-12 rounded-2xl bg-[#15271e] px-6 text-sm font-bold text-white" onClick={handleResume} type="button">
                Resume
              </button>
            ) : null}
            {phase !== "idle" ? (
              <button className="min-h-12 rounded-2xl border border-stone-300 px-6 text-sm font-semibold text-stone-700" onClick={handleFinish} type="button">
                Finish
              </button>
            ) : null}
          </div>

          <div className="mt-8 flex flex-col items-center gap-4">
            <button
              className="min-h-14 w-full max-w-xs rounded-2xl bg-[#d8ff62] text-lg font-bold text-[#15271e] disabled:cursor-not-allowed disabled:opacity-50"
              disabled={phase === "idle"}
              onClick={() => setFullRounds((value) => value + 1)}
              type="button"
            >
              + ROUND ({fullRounds})
            </button>
            <button
              className="min-h-11 w-full max-w-xs rounded-xl border border-stone-200 bg-[#fafaf7] text-xs font-semibold text-stone-700 disabled:opacity-50"
              disabled={phase === "idle" || fullRounds === 0}
              onClick={() => setFullRounds((value) => Math.max(0, value - 1))}
              type="button"
            >
              − Round
            </button>
            <div className="grid w-full max-w-xs grid-cols-3 gap-2">
              <div className="flex min-h-11 items-center justify-between rounded-xl border border-stone-200 bg-[#fafaf7] px-2 text-xs font-semibold text-stone-700">
                <button
                  aria-label="Decrease pull-ups"
                  className="min-h-8 min-w-8 rounded-lg text-stone-500 disabled:opacity-30"
                  disabled={phase === "idle" || extraPullups === 0}
                  onClick={() => setExtraPullups((v) => Math.max(0, v - 1))}
                  type="button"
                >
                  −
                </button>
                <span className="px-1 text-center">Pull-ups ({extraPullups})</span>
                <button
                  aria-label="Increase pull-ups"
                  className="min-h-8 min-w-8 rounded-lg text-stone-500 disabled:opacity-30"
                  disabled={phase === "idle"}
                  onClick={() => setExtraPullups((v) => v + 1)}
                  type="button"
                >
                  +
                </button>
              </div>
              <div className="flex min-h-11 items-center justify-between rounded-xl border border-stone-200 bg-[#fafaf7] px-2 text-xs font-semibold text-stone-700">
                <button
                  aria-label="Decrease push-ups"
                  className="min-h-8 min-w-8 rounded-lg text-stone-500 disabled:opacity-30"
                  disabled={phase === "idle" || extraPushups === 0}
                  onClick={() => setExtraPushups((v) => Math.max(0, v - 1))}
                  type="button"
                >
                  −
                </button>
                <span className="px-1 text-center">Push-ups ({extraPushups})</span>
                <button
                  aria-label="Increase push-ups"
                  className="min-h-8 min-w-8 rounded-lg text-stone-500 disabled:opacity-30"
                  disabled={phase === "idle"}
                  onClick={() => setExtraPushups((v) => v + 1)}
                  type="button"
                >
                  +
                </button>
              </div>
              <div className="flex min-h-11 items-center justify-between rounded-xl border border-stone-200 bg-[#fafaf7] px-2 text-xs font-semibold text-stone-700">
                <button
                  aria-label="Decrease squats"
                  className="min-h-8 min-w-8 rounded-lg text-stone-500 disabled:opacity-30"
                  disabled={phase === "idle" || extraSquats === 0}
                  onClick={() => setExtraSquats((v) => Math.max(0, v - 1))}
                  type="button"
                >
                  −
                </button>
                <span className="px-1 text-center">Squats ({extraSquats})</span>
                <button
                  aria-label="Increase squats"
                  className="min-h-8 min-w-8 rounded-lg text-stone-500 disabled:opacity-30"
                  disabled={phase === "idle"}
                  onClick={() => setExtraSquats((v) => v + 1)}
                  type="button"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        </>
      ) : (
        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <p className="text-center text-sm text-stone-600">
            {fullRounds} full rounds · {extraPullups + extraPushups + extraSquats} partial reps · {formatClock((finalSeconds ?? 0) * 1000)} elapsed
          </p>

          <div className="grid grid-cols-2 gap-3">
            <label className="text-xs font-semibold text-stone-500">
              RPE <span className="font-normal text-stone-400">(optional)</span>
              <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" max={10} min={1} name="rpe" type="number" />
            </label>
            <label className="text-xs font-semibold text-stone-500">
              Calories <span className="font-normal text-stone-400">(from device)</span>
              <input className="mt-1 min-h-12 w-full rounded-2xl border border-stone-300 px-4 text-base" min={0} name="caloriesBurned" type="number" />
            </label>
          </div>

          <label className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700">
            <input className="accent-[#789416]" name="estimateCalories" type="checkbox" />
            No device reading — estimate calories for me
          </label>

          <fieldset>
            <legend className="text-sm font-semibold text-stone-700">Visibility</legend>
            <div className="mt-2 flex gap-3">
              <label className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700">
                <input defaultChecked className="accent-[#789416]" name="visibility" type="radio" value="team" />
                Share with team
              </label>
              <label className="flex min-h-11 items-center gap-2 rounded-xl border border-stone-200 bg-[#fafaf7] px-3 text-sm text-stone-700">
                <input className="accent-[#789416]" name="visibility" type="radio" value="private" />
                Private
              </label>
            </div>
          </fieldset>

          <label className="block text-sm font-semibold text-stone-700">
            Notes <span className="font-normal text-stone-400">(optional)</span>
            <textarea className="mt-2 min-h-20 w-full rounded-2xl border border-stone-300 px-4 py-3 text-base" maxLength={2000} name="notes" />
          </label>

          {error ? <p aria-live="polite" className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</p> : null}

          <button
            className="min-h-12 w-full rounded-2xl bg-[#15271e] px-5 py-3 text-sm font-bold text-white disabled:cursor-wait disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Saving…" : "Save result"}
          </button>
        </form>
      )}
    </div>
  );
}
